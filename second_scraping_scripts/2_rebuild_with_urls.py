"""
rebuild_with_urls.py
Builds the FAISS index from all scraped ZIP files.

Rules:
- Only index rows that have a valid URL (http/https)
- Skip excluded Facebook navigation URLs
- No content-only rows (no URL = skip)
- Global URL deduplication across all non-book sources
- Books (pdf_evidence_scraped.zip) are never deduplicated
"""

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

# ── Paths ─────────────────────────────────────────────────────────────────────
ZIP_FILES = [
    r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\1421FacebookWebsite\facebook_pages_csv.zip",
    r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\1421FacebookWebsite\facebook_posts.zip",
    r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\1421FoundationWebsite\1421_foundation_scraped.zip",
    r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\GavinMenziesWebsite\1421_evidence_scraped.zip",
    r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\GavinMenziesWebsite\1434_evidence_scraped.zip",
    r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\GavinMenziesWebsite\america_evidence_scraped.zip",
    r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\GavinMenziesWebsite\atlantis_evidence_scraped.zip",
    r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\GavinMenziesWebsite\gavin_menzies_scraped.zip",
    r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\3BooksAndMore\pdf_evidence_scraped.zip",
]

OUTPUT_DIR      = Path(r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\data\vector_databases\main_index")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
BOOK_ZIP_NAME   = "pdf_evidence_scraped.zip"

# ── Excluded Facebook nav URLs ────────────────────────────────────────────────
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
}

URL_RE = re.compile(r'https?://\S+|www\.\S+', re.IGNORECASE)

# ── Helpers ───────────────────────────────────────────────────────────────────

def is_excluded(url):
    if not url:
        return False
    return url.strip().rstrip("/") in {u.rstrip("/") for u in EXCLUDED_URLS}

def valid_url(raw):
    s = (raw or "").strip()
    return s if s.startswith(("http://", "https://")) else ""

def is_fb_posts(z): return "facebook_posts" in z.lower()
def is_fb_pages(z): return "facebook" in z.lower() and "page" in z.lower()
def is_fb_any(z):   return "facebook" in z.lower()

def default_author(zip_name):
    z = zip_name.lower()
    if "facebook" in z:        return "1421 Foundation (Facebook)"
    if "1421_foundation" in z: return "1421 Foundation (Website)"
    return "Gavin Menzies"

def col_map(cols):
    return {str(c).lower(): c for c in cols}

def find_col(cols, *keywords):
    cm = col_map(cols)
    for kw in keywords:
        if kw in cm:
            return cm[kw]
    for kw in keywords:
        for c in cols:
            if kw in str(c).lower():
                return c
    return None

def get_val(row, col):
    if col is None:
        return ""
    v = row.get(col, "")
    if pd.isna(v):
        return ""
    return str(v).strip()

def pick_url_col(cols, zip_name):
    """
    Facebook posts  → post_url (the post permalink, not the shared link)
    Facebook pages  → page_url / source_url / url
    Everything else → source_url / url / link
    """
    cm = col_map(cols)

    if is_fb_posts(zip_name):
        for name in ("post_url", "permalink", "post_link", "post_permalink"):
            if name in cm:
                return cm[name], f"post permalink ({cm[name]})"
        for c in cols:
            if "post" in str(c).lower() and "url" in str(c).lower():
                return c, f"post+url fallback ({c})"
        return None, "NONE — no post_url col"

    if is_fb_pages(zip_name):
        for name in ("page_url", "source_url", "url", "link", "page_link", "permalink"):
            if name in cm:
                return cm[name], f"page url ({cm[name]})"
        for c in cols:
            if "url" in str(c).lower():
                return c, f"url fallback ({c})"
        return None, "NONE"

    # Non-Facebook (books, evidence sites, 1421 Foundation website)
    for name in ("source_url", "document_url", "url", "link", "page_url", "post_url", "source"):
        if name in cm:
            return cm[name], f"standard ({cm[name]})"
    for c in cols:
        if "url" in str(c).lower():
            return c, f"url fallback ({c})"
    return None, "NONE"

def strip_urls(text):
    cleaned = URL_RE.sub("", text or "")
    cleaned = re.sub(r'\s*[:|]\s*$', '', cleaned)
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)
    return cleaned.strip().rstrip(".,;:-\u2013\u2014")

def clean_title(raw):
    if not raw:
        return ""
    t = strip_urls(raw.strip())
    if not t:
        return ""
    # Remove back-to-back duplicate: "Gavin MenziesGavin Menzies"
    half = len(t) // 2
    if half > 10 and t[:half] == t[half:]:
        t = t[:half].strip()
    # Remove word-level duplicate: "Gavin Menzies Gavin Menzies"
    words = t.split()
    mid = len(words) // 2
    if mid > 0 and words[:mid] == words[mid:]:
        t = " ".join(words[:mid]).strip()
    # Discard if it is just an author name
    if re.fullmatch(
        r"(Gavin Menzies|1421 Foundation|The 1421 Foundation|"
        r"1421 Foundation \(Facebook\)|1421 Foundation \(Website\))",
        t, re.IGNORECASE
    ):
        return ""
    return t.strip(".,;:-\u2013\u2014")[:400] or ""

def title_from_content(content, fallback):
    if not content or not content.strip():
        return fallback[:400]
    text = re.sub(
        r"^(Title|Author|Content|Source|Type|Tags)\s*:\s*",
        "", content.strip(), flags=re.IGNORECASE
    ).strip()
    if not text:
        return fallback[:400]
    parts = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)
    first = parts[0].strip()
    if len(first) < 15:
        first = text[:200].strip()
    elif len(first) > 300:
        first = first[:300].strip()
    first = strip_urls(first).rstrip(".,;:")
    if not first or len(first) < 5:
        return fallback[:400]
    return first[:400]

def read_csv(zip_ref, name):
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            with zip_ref.open(name) as f:
                return pd.read_csv(f, encoding=enc)
        except Exception:
            continue
    return None

# ── Process one CSV ───────────────────────────────────────────────────────────

def process_csv(df, csv_filename, zip_name):
    """
    Returns a list of document dicts.
    Only rows with a valid URL are kept — no URL = skip.
    No within-zip deduplication here; global URL dedup happens later.
    Books get no dedup at all.
    """
    docs = []
    if df is None or len(df) == 0:
        return docs

    cols    = list(df.columns)
    is_book = zip_name == BOOK_ZIP_NAME
    is_fb   = is_fb_any(zip_name)

    content_col = find_col(cols, "full_content", "content", "post_content",
                            "page_content", "text", "body", "section")
    title_col   = find_col(cols, "title", "document_title", "name",
                            "post_title", "page_title")
    author_col  = find_col(cols, "author", "posted_by", "creator", "post_author")
    url_col, url_desc = pick_url_col(cols, zip_name)

    auth_default = default_author(zip_name)

    if is_fb or is_book:
        tag = ("[BOOKS]"    if is_book
               else "[FB-POSTS]" if is_fb_posts(zip_name)
               else "[FB-PAGES]")
        print(f"      {tag} {Path(csv_filename).name}")
        print(f"        cols   : {cols}")
        print(f"        content: {content_col} | title: {title_col} | url: {url_desc}")

    skipped = {"no_url": 0, "excluded": 0}

    for _, row in df.iterrows():
        url = valid_url(get_val(row, url_col))

        # No URL → skip
        if not url:
            skipped["no_url"] += 1
            continue

        # Excluded nav page → skip
        if is_excluded(url):
            skipped["excluded"] += 1
            continue

        content = get_val(row, content_col)

        # Author
        raw_author = get_val(row, author_col)
        if raw_author and len(raw_author) > 1:
            author = clean_title(raw_author) or auth_default
        else:
            author = auth_default

        # Title
        raw_title = get_val(row, title_col)
        cleaned   = clean_title(raw_title)
        if len(cleaned) > 300 or (len(cleaned.split()) > 40 and "Evidence" in cleaned):
            cleaned = ""
        if cleaned:
            title = cleaned
        else:
            title = title_from_content(content, f"Document from {Path(csv_filename).stem}")

        content_text = content if content else f"Source: {url}"

        docs.append({
            "title":        title,
            "url":          url[:500],
            "author":       author[:200],
            "source_type":  "book" if is_book else "web",
            "source_file":  Path(csv_filename).name,
            "source_zip":   zip_name,
            "content_text": content_text,
        })

    print(f"        kept={len(docs)} | no_url={skipped['no_url']} | excluded={skipped['excluded']}")
    return docs

# ── Process one ZIP ───────────────────────────────────────────────────────────

def process_zip(zip_path):
    docs = []
    if not Path(zip_path).exists():
        print(f"  WARNING: not found — {zip_path}")
        return docs

    zip_name = Path(zip_path).name
    print(f"\n  Processing {zip_name}...")

    with zipfile.ZipFile(zip_path, "r") as zf:
        csv_files = [
            f for f in zf.namelist()
            if f.lower().endswith(".csv")
            and not any(x in f.lower() for x in
                        ["summary", "error", "mapping", "log", "all_books"])
        ]
        print(f"    {len(csv_files)} CSV file(s)")

        for csv_file in csv_files:
            df = read_csv(zf, csv_file)
            if df is not None and len(df) > 0:
                file_docs = process_csv(df, csv_file, zip_name)
                print(f"      -> {len(file_docs)} rows from {Path(csv_file).name}")
                docs.extend(file_docs)

    print(f"    Total from {zip_name}: {len(docs)}")
    return docs

# ── Global URL deduplication ──────────────────────────────────────────────────

def deduplicate(documents):
    """
    Deduplicate by URL across all non-book sources.
    Books are kept as-is (multiple pages per book, same base URL is fine).
    """
    seen = set()
    unique = []
    dropped = 0

    for doc in documents:
        if doc["source_zip"] == BOOK_ZIP_NAME:
            unique.append(doc)
            continue
        url = doc["url"]
        if url not in seen:
            seen.add(url)
            unique.append(doc)
        else:
            dropped += 1

    print(f"  Global dedup: removed {dropped}, kept {len(unique)}")
    return unique

# ── Build FAISS index ─────────────────────────────────────────────────────────

def build_index(documents, output_dir):
    print(f"\n  Loading model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    raw_texts   = []
    metadatas   = []
    embed_texts = []

    for doc in documents:
        raw_texts.append(doc["content_text"])
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
            f"Title: {doc['title']} Author: {doc['author']} "
            f"Content: {doc['content_text'][:500]}"
        )

    print(f"  Embedding {len(embed_texts)} documents...")
    embeddings = model.encode(
        embed_texts,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
        batch_size=64,
    ).astype("float32")

    dim   = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    output_dir.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(output_dir / "faiss_index.bin"))
    print(f"  Saved index    -> {output_dir / 'faiss_index.bin'}")

    with open(output_dir / "faiss_metadata.pkl", "wb") as f:
        pickle.dump({"documents": raw_texts, "metadatas": metadatas}, f)
    print(f"  Saved metadata -> {output_dir / 'faiss_metadata.pkl'}")

    breakdown = {}
    for doc in documents:
        breakdown[doc["source_zip"]] = breakdown.get(doc["source_zip"], 0) + 1

    with open(output_dir / "database_stats.json", "w") as f:
        json.dump({
            "document_count":      len(documents),
            "embedding_dimension": dim,
            "embedding_model":     EMBEDDING_MODEL,
            "created_at":          datetime.now().isoformat(),
            "source_breakdown":    breakdown,
        }, f, indent=2)
    print(f"  Saved stats    -> {output_dir / 'database_stats.json'}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  REBUILD INDEX")
    print("=" * 60)

    all_docs = []

    print("\nStep 1: Reading ZIPs...")
    for zip_path in ZIP_FILES:
        docs = process_zip(zip_path)
        all_docs.extend(docs)
        print(f"  Running total: {len(all_docs)}")

    print(f"\nBefore dedup: {len(all_docs)}")
    print("\nStep 2: Deduplication...")
    all_docs = deduplicate(all_docs)
    print(f"After dedup:  {len(all_docs)}")

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
    print(f"URLs in titles: {len(url_in_title)}  (should be 0)")
    for d in url_in_title[:5]:
        print(f"  [{d['source_zip']}] {d['title'][:100]}")

    breakdown = {}
    for d in all_docs:
        breakdown[d["source_zip"]] = breakdown.get(d["source_zip"], 0) + 1
    print("\nSource breakdown:")
    for z, n in sorted(breakdown.items()):
        print(f"  {z}: {n}")

    print("\nStep 3: Building FAISS index...")
    build_index(all_docs, OUTPUT_DIR)

    print("\n" + "=" * 60)
    print(f"  DONE — {len(all_docs)} documents")
    print("=" * 60)
    print(f"\nOutput: {OUTPUT_DIR}")
    print("Copy faiss_index.bin + faiss_metadata.pkl to")


if __name__ == "__main__":
    main()