import re
import sys
import zipfile
import pickle
import json
import faiss
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("ERROR: pip install sentence-transformers")
    sys.exit(1)

ZIP_FILES = [
    r"C:\Users\ibrah\PycharmProjects\PythonProject12\raw_csvs\1421FacebookWebsite\facebook_pages_csv.zip",
    r"C:\Users\ibrah\PycharmProjects\PythonProject12\raw_csvs\1421FacebookWebsite\facebook_posts.zip",
    r"C:\Users\ibrah\PycharmProjects\PythonProject12\raw_csvs\1421FoundationWebsite\1421_foundation_scraped.zip",
    r"C:\Users\ibrah\PycharmProjects\PythonProject12\raw_csvs\GavinMenziesWebsite\1421_evidence_scraped.zip",
    r"C:\Users\ibrah\PycharmProjects\PythonProject12\raw_csvs\GavinMenziesWebsite\1434_evidence_scraped.zip",
    r"C:\Users\ibrah\PycharmProjects\PythonProject12\raw_csvs\GavinMenziesWebsite\america_evidence_scraped.zip",
    r"C:\Users\ibrah\PycharmProjects\PythonProject12\raw_csvs\GavinMenziesWebsite\atlantis_evidence_scraped.zip",
    r"C:\Users\ibrah\PycharmProjects\PythonProject12\raw_csvs\GavinMenziesWebsite\gavin_menzies_scraped.zip",
    r"C:\Users\ibrah\PycharmProjects\PythonProject12\raw_csvs\All Three Books\pdf_evidence_scraped.zip",
]

OUTPUT_DIR      = Path(r"C:\Users\ibrah\PycharmProjects\PythonProject12\scripts\vector_databases\main_index")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
BOOK_ZIP_NAME   = "pdf_evidence_scraped.zip"

EXCLUDED_URLS = {
    "https://www.facebook.com/1421foundation/",
    "https://www.facebook.com/1421foundation/about",
    "https://www.facebook.com/1421foundation/directory_category",
    "https://www.facebook.com/1421foundation/directory_basic_info",
    "https://www.facebook.com/1421foundation/directory_links",
    "https://www.facebook.com/1421foundation/directory_contact_info",
    "https://www.facebook.com/1421foundation/directory_privacy_and_legal_info",
    "https://www.facebook.com/1421foundation/followers",
    "https://www.facebook.com/1421foundation/following",
    "https://www.facebook.com/1421foundation/photos",
    "https://www.facebook.com/1421foundation/photos_of",
    "https://www.facebook.com/1421foundation/photos_albums",
    "https://www.facebook.com/1421foundation/mentions",
    "https://www.facebook.com/1421foundation/live_videos",
    "https://www.facebook.com/1421foundation/map",
    "https://www.facebook.com/1421foundation/likes",
    "https://www.facebook.com/1421foundation/reviews_given",
    "https://www.gavinmenzies.net/china/gallery/shipwreck/",
}

URL_RE = re.compile(r'https?://\S+|www\.\S+', re.IGNORECASE)

def is_excluded_url(url):
    if not url: return False
    return any(url.strip().rstrip("/") == ex.rstrip("/") for ex in EXCLUDED_URLS)

def _valid_url(raw):
    s = (raw or "").strip()
    return s if s.startswith(("http://", "https://")) else ""

def _is_fb_posts(z):  return "facebook_posts" in z.lower()
def _is_fb_pages(z):  return "facebook" in z.lower() and "page" in z.lower()
def _is_fb_any(z):    return "facebook" in z.lower()
def _is_links_csv(f): return f.lower().endswith("_links.csv")

def _default_author(zip_name):
    z = zip_name.lower()
    if "facebook" in z:        return "1421 Foundation (Facebook)"
    if "1421_foundation" in z: return "1421 Foundation (Website)"
    return "Gavin Menzies"

def _col_map(cols):
    return {str(c).lower(): c for c in cols}

def _pick_url_col(cols, zip_name, csv_filename):
    """
    URL column priority:
    - _links.csv files (from Facebook posts): link_url = the actual article URL
    - facebook_posts main CSVs: post_url = the FB post permalink
    - facebook_pages CSVs: page_url > source_url > url
    - books: source_url
    - everything else: source_url > url > link
    """
    cm = _col_map(cols)
    fname = csv_filename.lower()

    # _links.csv files — the external article linked from a post
    if _is_links_csv(fname):
        for c in ("link_url", "url", "link", "source_url"):
            if c in cm:
                return cm[c], f"link article url ({cm[c]})"
        return None, "NONE — no url col in links csv"

    if _is_fb_posts(zip_name):
        for c in ("post_url", "permalink", "post_link"):
            if c in cm:
                return cm[c], f"post permalink ({cm[c]})"
        return None, "NONE — no post_url"

    if _is_fb_pages(zip_name):
        for c in ("page_url", "source_url", "url", "link"):
            if c in cm:
                return cm[c], f"page url ({cm[c]})"
        for col in cols:
            if "url" in str(col).lower():
                return col, f"url fallback ({col})"
        return None, "NONE"

    # books and everything else
    for c in ("source_url", "document_url", "url", "link", "page_url", "post_url"):
        if c in cm:
            return cm[c], f"standard ({cm[c]})"
    for col in cols:
        if "url" in str(col).lower():
            return col, f"url fallback ({col})"
    return None, "NONE"

def _find_col(cols, *keywords):
    cm = _col_map(cols)
    for kw in keywords:
        if kw in cm: return cm[kw]
    for kw in keywords:
        for col in cols:
            if kw in str(col).lower(): return col
    return None

def _val(row, col):
    if col is None: return ""
    v = row.get(col, "")
    if pd.isna(v): return ""
    return str(v).strip()

def _strip_urls(text):
    cleaned = URL_RE.sub("", text or "")
    cleaned = re.sub(r'\s*[:|]\s*$', '', cleaned)
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)
    return cleaned.strip().rstrip(".,;:-\u2013\u2014")

def _clean_title(raw):
    if not raw: return ""
    t = _strip_urls(raw.strip())
    if not t: return ""
    half = len(t) // 2
    if half > 10 and t[:half] == t[half:]:
        t = t[:half].strip()
    words = t.split()
    mid = len(words) // 2
    if mid > 0 and words[:mid] == words[mid:]:
        t = " ".join(words[:mid]).strip()
    if re.fullmatch(
        r"(Gavin Menzies|1421 Foundation|The 1421 Foundation|"
        r"1421 Foundation \(Facebook\)|1421 Foundation \(Website\))",
        t, re.IGNORECASE,
    ):
        return ""
    t = t.strip(".,;:-\u2013\u2014")
    return t[:400] if t else ""

def _title_from_content(content, fallback):
    if not content or not content.strip(): return fallback[:400]
    text = re.sub(
        r"^(Title|Author|Content|Source|Type|Tags)\s*:\s*",
        "", content.strip(), flags=re.IGNORECASE,
    ).strip()
    if not text: return fallback[:400]
    parts = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)
    first = parts[0].strip()
    if len(first) < 15:   first = text[:200].strip()
    elif len(first) > 300: first = first[:300].strip()
    first = _strip_urls(first).rstrip(".,;:")
    if not first or len(first) < 5: return fallback[:400]
    return first[:400]

def _read_csv(zip_ref, csv_filename):
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            with zip_ref.open(csv_filename) as f:
                return pd.read_csv(f, encoding=enc)
        except Exception:
            continue
    return None


def process_csv(df, csv_filename, zip_name, seen_titles_in_zip):
    """
    seen_titles_in_zip: shared set for title-dedup WITHIN a ZIP.
    For books, dedup key = title + page_number so each page is unique.
    For _links.csv, dedup key = url (each article link is its own document).
    """
    docs = []
    if df is None or len(df) == 0:
        return docs

    cols     = list(df.columns)
    is_book  = zip_name == BOOK_ZIP_NAME
    is_fb    = _is_fb_any(zip_name)
    is_links = _is_links_csv(csv_filename)

    content_col = _find_col(cols,
        "full_content", "content", "post_content", "page_content",
        "link_content", "text", "body", "section")
    title_col   = _find_col(cols,
        "title", "document_title", "name", "post_title", "page_title",
        "link_title")
    author_col  = _find_col(cols,
        "author", "posted_by", "creator", "post_author")
    page_col    = _find_col(cols, "page_number", "page")

    url_col, url_desc = _pick_url_col(cols, zip_name, csv_filename)

    default_author = _default_author(zip_name)

    if is_fb or is_book:
        tag = ("[BOOKS]" if is_book
               else "[FB-LINKS]" if is_links
               else "[FB-POSTS]" if _is_fb_posts(zip_name)
               else "[FB-PAGES]")
        print(f"      {tag} {Path(csv_filename).name}")
        print(f"        cols: {cols}")
        print(f"        content={content_col} | title={title_col} | url={url_desc}")

    skipped = {"no_url": 0, "excluded": 0, "dup": 0}

    for idx, row in df.iterrows():
        content = _val(row, content_col)
        url     = _valid_url(_val(row, url_col))

        # Rule 1: no valid URL → skip
        if not url:
            skipped["no_url"] += 1
            continue

        # Rule 2: excluded nav page → skip
        if is_excluded_url(url):
            skipped["excluded"] += 1
            continue

        # Author
        raw_author = _val(row, author_col)
        if raw_author and len(raw_author) > 1:
            cleaned_author = _clean_title(raw_author)
            author = cleaned_author if cleaned_author else default_author
        else:
            author = default_author

        # Title
        raw_title = _val(row, title_col)
        cleaned   = _clean_title(raw_title)
        if len(cleaned) > 300 or (len(cleaned.split()) > 40 and "Evidence" in cleaned):
            cleaned = ""
        if cleaned:
            title = cleaned
        else:
            fallback = f"Document from {Path(csv_filename).stem}"
            title = _title_from_content(content, fallback)

        # Dedup key:
        #   books   → title + page_number  (so each page of a book is unique)
        #   links   → url                  (each linked article is unique)
        #   others  → title (lowercase)
        page_num = _val(row, page_col) if is_book else ""
        if is_book:
            dedup_key = f"{title.strip().lower()}|||page={page_num}"
        elif is_links:
            dedup_key = url  # URL-based dedup for linked articles
        else:
            dedup_key = title.strip().lower()

        if dedup_key and dedup_key in seen_titles_in_zip:
            skipped["dup"] += 1
            continue
        if dedup_key:
            seen_titles_in_zip.add(dedup_key)

        content_text = content if content else f"Source: {url}"

        docs.append({
            "title":        title,
            "url":          url[:500],
            "author":       author[:200],
            "source_type":  "book" if is_book else "web",
            "source_file":  Path(csv_filename).name,
            "source_zip":   zip_name,
            "content_text": content_text,
            "row_index":    idx,
        })

    print(f"        kept={len(docs)} | no_url={skipped['no_url']} | "
          f"excluded={skipped['excluded']} | dup={skipped['dup']}")
    return docs


def process_zip(zip_path):
    docs = []
    if not Path(zip_path).exists():
        print(f"  WARNING: ZIP not found — {Path(zip_path).name}")
        print(f"  Full path: {zip_path}")
        return docs

    zip_name = Path(zip_path).name
    print(f"\n  Processing {zip_name}...")

    seen_titles_in_zip = set()

    with zipfile.ZipFile(zip_path, "r") as zf:
        csv_files = [
            f for f in zf.namelist()
            if f.lower().endswith(".csv")
            and not any(x in f.lower() for x in
                        ["summary", "error", "mapping", "log", "all_books"])
        ]
        print(f"    {len(csv_files)} CSV file(s)")

        for csv_file in csv_files:
            df = _read_csv(zf, csv_file)
            if df is not None and len(df) > 0:
                file_docs = process_csv(df, csv_file, zip_name, seen_titles_in_zip)
                docs.extend(file_docs)

    print(f"    Total from {zip_name}: {len(docs)}")
    return docs


def deduplicate_by_url(documents):
    seen_urls = set()
    unique    = []
    dup_count = 0
    for doc in documents:
        if doc["source_zip"] == BOOK_ZIP_NAME:
            unique.append(doc)
            continue
        url = doc["url"]
        if url not in seen_urls:
            seen_urls.add(url)
            unique.append(doc)
        else:
            dup_count += 1
    print(f"  Global URL dedup: removed {dup_count}, kept {len(unique)}")
    return unique


def build_index(documents, output_dir):
    print(f"\n  Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    raw_texts   = []
    metadatas   = []
    embed_texts = []

    for doc in documents:
        content = doc["content_text"]
        raw_texts.append(content)
        metadatas.append({
            "title":       doc["title"],
            "url":         doc["url"],
            "author":      doc["author"],
            "source_type": doc["source_type"],
            "source_file": doc["source_file"],
            "year":        0,
            "tags":        [],
            "page":        None,
        })
        embed_texts.append(
            f"Title: {doc['title']} Author: {doc['author']} Content: {content[:500]}"
        )

    print(f"  Creating embeddings for {len(embed_texts)} documents...")
    embeddings = model.encode(
        embed_texts, show_progress_bar=True,
        convert_to_numpy=True, normalize_embeddings=True, batch_size=64,
    ).astype("float32")

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    output_dir.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(output_dir / "faiss_index.bin"))
    print(f"  Saved FAISS index  -> {output_dir / 'faiss_index.bin'}")

    with open(output_dir / "faiss_metadata.pkl", "wb") as f:
        pickle.dump({"documents": raw_texts, "metadatas": metadatas}, f)
    print(f"  Saved metadata     -> {output_dir / 'faiss_metadata.pkl'}")

    breakdown = {}
    for doc in documents:
        breakdown[doc["source_zip"]] = breakdown.get(doc["source_zip"], 0) + 1
    with open(output_dir / "database_stats.json", "w") as f:
        json.dump({
            "document_count": len(documents),
            "embedding_dimension": dimension,
            "embedding_model": EMBEDDING_MODEL,
            "created_at": datetime.now().isoformat(),
            "source_breakdown": breakdown,
        }, f, indent=2)
    print(f"  Saved stats        -> {output_dir / 'database_stats.json'}")


def main():
    print("=" * 60)
    print("  REBUILD — FINAL VERSION")
    print("=" * 60)

    all_docs = []
    print("\nStep 1: Reading ZIP files...")
    for zip_path in ZIP_FILES:
        docs = process_zip(zip_path)
        all_docs.extend(docs)
        print(f"  Running total: {len(all_docs)}")

    print(f"\nTotal before URL dedup: {len(all_docs)}")
    print("\nStep 2: Global URL deduplication...")
    all_docs = deduplicate_by_url(all_docs)
    print(f"Total after URL dedup:  {len(all_docs)}")

    # Diagnostics
    by_author = {}
    for d in all_docs:
        by_author[d["author"]] = by_author.get(d["author"], 0) + 1
    print("\nAuthor breakdown:")
    for a, n in sorted(by_author.items()):
        print(f"  {a}: {n}")

    no_url = [d for d in all_docs if not d["url"]]
    print(f"\nDocuments with no URL: {len(no_url)}  (should be 0)")

    url_in_title = [d for d in all_docs
                    if "http" in d["title"].lower() or "www." in d["title"].lower()]
    print(f"Titles still containing URLs: {len(url_in_title)}  (should be 0)")
    for d in url_in_title[:5]:
        print(f"  [{d['source_zip']}] {d['title'][:100]}")

    breakdown = {}
    for d in all_docs:
        breakdown[d["source_zip"]] = breakdown.get(d["source_zip"], 0) + 1
    print("\nSource breakdown:")
    for k, v in sorted(breakdown.items()):
        print(f"  {k}: {v}")

    print("\nStep 3: Building FAISS index...")
    build_index(all_docs, OUTPUT_DIR)

    print("\n" + "=" * 60)
    print(f"  DONE — {len(all_docs)} documents indexed")
    print("=" * 60)
    print(f"\nOutput: {OUTPUT_DIR}")
    print("\nNext: copy faiss_index.bin + faiss_metadata.pkl to")
    print("      backend/data/vector_databases/main_index/ and redeploy Koyeb.")

if __name__ == "__main__":
    main()