import os
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
    print("ERROR: sentence_transformers not installed.")
    print("Run: pip install sentence-transformers")
    sys.exit(1)

# ── PATHS ────────────────────────────────────────────────────────────────────
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

OUTPUT_DIR = Path(r"C:\Users\ibrah\PycharmProjects\PythonProject12\scripts\vector_databases\main_index")
# ─────────────────────────────────────────────────────────────────────────────

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
BOOK_ZIP_NAME   = "pdf_evidence_scraped.zip"

# Facebook nav pages — excluded (not content)
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

def is_excluded_url(url: str) -> bool:
    if not url:
        return False
    clean = url.strip().rstrip("/")
    return any(clean == ex.rstrip("/") for ex in EXCLUDED_URLS)

# ── Source classification ─────────────────────────────────────────────────────

def _is_facebook_posts_zip(zip_name: str) -> bool:
    return "facebook_posts" in zip_name.lower()

def _is_facebook_pages_zip(zip_name: str) -> bool:
    z = zip_name.lower()
    return "facebook" in z and "pages" in z

def _is_facebook_zip(zip_name: str) -> bool:
    return "facebook" in zip_name.lower()

def _default_author(zip_name: str) -> str:
    z = zip_name.lower()
    if "facebook" in z:
        return "1421 Foundation (Facebook)"
    if "1421_foundation" in z:
        return "1421 Foundation (Website)"
    return "Gavin Menzies"

# ── Title cleaning ────────────────────────────────────────────────────────────

def _clean_title(raw: str) -> str:
    if not raw:
        return ""
    t = raw.strip()

    # Back-to-back duplicate without space: "Gavin MenziesGavin Menzies"
    half = len(t) // 2
    if half > 10 and t[:half] == t[half:]:
        t = t[:half].strip()

    # Word-level duplicate: "Gavin Menzies Gavin Menzies"
    words = t.split()
    mid = len(words) // 2
    if mid > 0 and words[:mid] == words[mid:]:
        t = " ".join(words[:mid]).strip()

    # Title that is just an author name → discard
    if re.fullmatch(
        r"(Gavin Menzies|1421 Foundation|The 1421 Foundation|"
        r"1421 Foundation \(Facebook\)|1421 Foundation \(Website\))",
        t, re.IGNORECASE
    ):
        return ""

    t = t.strip(".,;:-–—")
    return t[:400] if t else ""

def _title_from_content(content: str, fallback: str) -> str:
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
    first = first.rstrip(".,;:")
    return first[:400] if first else fallback[:400]

# ── CSV helpers ───────────────────────────────────────────────────────────────

def _read_csv(zip_ref, csv_filename: str):
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            with zip_ref.open(csv_filename) as f:
                return pd.read_csv(f, encoding=enc)
        except Exception:
            continue
    return None

def _find_col(columns, *keywords):
    """Return the first column whose lowercase name contains any keyword (exact priority order)."""
    for kw in keywords:
        for col in columns:
            if str(col).lower() == kw:        # exact match first
                return col
        for col in columns:
            if kw in str(col).lower():         # then substring match
                return col
    return None

def _val(row, col) -> str:
    if col is None:
        return ""
    v = row.get(col, "")
    if pd.isna(v):
        return ""
    return str(v).strip()

def _valid_url(raw: str) -> str:
    """Return the URL if it starts with http, else empty string."""
    s = raw.strip()
    return s if s.startswith(("http://", "https://")) else ""

# ── URL column selection per source ──────────────────────────────────────────

def _pick_url_col(cols: list, zip_name: str) -> str | None:
    """
    For Facebook posts: return post_url column (the permalink to the post itself).
    For Facebook pages: return page_url column.
    For everything else: use source_url > url > link > document_url order.

    This prevents the generic 'url' column (which holds the external link
    shared inside a post) from being used as the document's source URL.
    """
    col_names_lower = {str(c).lower(): c for c in cols}

    if _is_facebook_posts_zip(zip_name):
        # Explicit priority: post_url only.
        # The 'url' column in facebook_posts contains the external shared link,
        # which is NOT the permalink to the post — we deliberately skip it.
        for candidate in ("post_url",):
            if candidate in col_names_lower:
                return col_names_lower[candidate]
        # Fallback: any column with 'post' and 'url' in the name
        for col in cols:
            c = str(col).lower()
            if "post" in c and "url" in c:
                return col
        return None  # No post URL found — better to have no URL than wrong URL

    if _is_facebook_pages_zip(zip_name):
        for candidate in ("page_url", "post_url", "source_url", "url"):
            if candidate in col_names_lower:
                return col_names_lower[candidate]
        return None

    # Non-Facebook: standard priority
    for candidate in ("source_url", "document_url", "url", "link"):
        if candidate in col_names_lower:
            return col_names_lower[candidate]
    return None

# ── Process one CSV ───────────────────────────────────────────────────────────

def process_csv(df, csv_filename: str, zip_name: str) -> list:
    docs = []
    if df is None or len(df) == 0:
        return docs

    cols    = list(df.columns)
    is_book = zip_name == BOOK_ZIP_NAME

    content_col = _find_col(cols, "full_content", "content", "post_content", "page_content", "text", "body")
    title_col   = _find_col(cols, "title", "document_title", "name", "post_title", "page_title")
    author_col  = _find_col(cols, "author", "posted_by", "creator", "post_author")

    # ── URL column — the key fix ──────────────────────────────────────
    url_col = _pick_url_col(cols, zip_name)

    if is_book:
        print(f"      [BOOKS] Columns in {csv_filename}: {cols}")
    elif _is_facebook_posts_zip(zip_name):
        print(f"      [FB POSTS] URL col → '{url_col}' | Columns: {cols}")
    elif _is_facebook_pages_zip(zip_name):
        print(f"      [FB PAGES] URL col → '{url_col}' | Columns: {cols}")

    default_author = _default_author(zip_name)
    skipped = {"excluded": 0, "empty": 0}

    for idx, row in df.iterrows():
        content = _val(row, content_col)
        url     = _valid_url(_val(row, url_col))

        if is_excluded_url(url):
            skipped["excluded"] += 1
            continue

        if not url and len(content) < 20:
            skipped["empty"] += 1
            continue

        # ── Author ────────────────────────────────────────────────────
        raw_author = _val(row, author_col)
        if raw_author and len(raw_author) > 1:
            cleaned_author = _clean_title(raw_author)
            author = cleaned_author if cleaned_author else default_author
        else:
            author = default_author

        # ── Title ─────────────────────────────────────────────────────
        raw_title = _val(row, title_col)
        cleaned   = _clean_title(raw_title)

        if len(cleaned) > 300 or (len(cleaned.split()) > 40 and "Evidence" in cleaned):
            cleaned = ""

        if cleaned:
            title = cleaned
        else:
            fallback = f"Document from {Path(csv_filename).stem}"
            title = _title_from_content(content, fallback)

        # ── Content ───────────────────────────────────────────────────
        content_text = content if content else (f"Source: {url}" if url else "[No content available]")

        docs.append({
            "title":        title,
            "url":          url[:500] if url else "",
            "author":       author[:200],
            "source_type":  "book" if is_book else "web",
            "source_file":  Path(csv_filename).name,
            "source_zip":   zip_name,
            "content_text": content_text,
            "row_index":    idx,
        })

    if skipped["excluded"]:
        print(f"      Skipped {skipped['excluded']} excluded Facebook nav URLs")
    if skipped["empty"]:
        print(f"      Skipped {skipped['empty']} rows with no URL and no content")

    return docs

# ── Process one ZIP ───────────────────────────────────────────────────────────

def process_zip(zip_path: str) -> list:
    docs = []
    if not Path(zip_path).exists():
        print(f"  WARNING: ZIP not found — {Path(zip_path).name}")
        return docs

    zip_name = Path(zip_path).name
    print(f"\n  Processing {zip_name}…")

    with zipfile.ZipFile(zip_path, "r") as zf:
        csv_files = [
            f for f in zf.namelist()
            if f.lower().endswith(".csv")
            and not any(x in f.lower() for x in ["summary", "error", "mapping", "log", "all_books"])
        ]
        print(f"    {len(csv_files)} CSV file(s) found")

        for csv_file in csv_files:
            df = _read_csv(zf, csv_file)
            if df is not None and len(df) > 0:
                file_docs = process_csv(df, csv_file, zip_name)
                print(f"      {Path(csv_file).name}: {len(file_docs)} rows kept")
                docs.extend(file_docs)

    print(f"    Total from {zip_name}: {len(docs)}")
    return docs

# ── Deduplication ─────────────────────────────────────────────────────────────

def deduplicate(documents: list) -> list:
    seen_urls: set = set()
    unique    = []
    dup_count = 0

    for doc in documents:
        if doc["source_zip"] == BOOK_ZIP_NAME:
            unique.append(doc)
            continue

        url = doc.get("url", "")
        if url:
            if url not in seen_urls:
                seen_urls.add(url)
                unique.append(doc)
            else:
                dup_count += 1
        else:
            key = f"{doc['title']}|{doc['source_file']}"
            if key not in seen_urls:
                seen_urls.add(key)
                unique.append(doc)
            else:
                dup_count += 1

    print(f"  Deduplication: removed {dup_count}, kept {len(unique)}")
    return unique

# ── Build FAISS index ─────────────────────────────────────────────────────────

def build_index(documents: list, output_dir: Path) -> None:
    """
    Pickle format main.py expects:
        {"documents": [raw_content_str, ...], "metadatas": [{...}, ...]}
    """
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

    print(f"  Creating embeddings for {len(embed_texts)} documents…")
    embeddings = model.encode(
        embed_texts,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
        batch_size=64,
    ).astype("float32")

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    output_dir.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(output_dir / "faiss_index.bin"))
    print(f"  Saved FAISS index  → {output_dir / 'faiss_index.bin'}")

    with open(output_dir / "faiss_metadata.pkl", "wb") as f:
        pickle.dump({"documents": raw_texts, "metadatas": metadatas}, f)
    print(f"  Saved metadata     → {output_dir / 'faiss_metadata.pkl'}")

    source_breakdown: dict = {}
    for doc in documents:
        k = doc["source_zip"]
        source_breakdown[k] = source_breakdown.get(k, 0) + 1

    with open(output_dir / "database_stats.json", "w") as f:
        json.dump({
            "document_count":      len(documents),
            "embedding_dimension": dimension,
            "embedding_model":     EMBEDDING_MODEL,
            "created_at":          datetime.now().isoformat(),
            "source_breakdown":    source_breakdown,
        }, f, indent=2)
    print(f"  Saved stats        → {output_dir / 'database_stats.json'}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  REBUILD — FINAL VERSION")
    print("=" * 60)

    all_docs: list = []

    print("\nStep 1: Reading all ZIP files…")
    for zip_path in ZIP_FILES:
        docs = process_zip(zip_path)
        all_docs.extend(docs)
        print(f"  Running total: {len(all_docs)}")

    print(f"\nTotal before deduplication: {len(all_docs)}")
    print("\nStep 2: Deduplicating…")
    all_docs = deduplicate(all_docs)
    print(f"Total after deduplication:  {len(all_docs)}")

    # ── Diagnostics ───────────────────────────────────────────────────
    by_author: dict = {}
    for d in all_docs:
        by_author[d["author"]] = by_author.get(d["author"], 0) + 1
    print("\nAuthor breakdown:")
    for a, n in sorted(by_author.items()):
        print(f"  {a}: {n}")

    no_author = [d for d in all_docs if not d["author"]]
    print(f"\nDocuments with no author: {len(no_author)} (should be 0)")

    # Spot-check Facebook post URLs
    fb_posts = [d for d in all_docs if "facebook_posts" in d["source_zip"].lower()]
    fb_with_url = [d for d in fb_posts if d["url"]]
    fb_non_fb_url = [d for d in fb_with_url if "facebook.com" not in d["url"]]
    print(f"\nFacebook posts:          {len(fb_posts)}")
    print(f"  With a URL:            {len(fb_with_url)}")
    print(f"  Non-Facebook URLs:     {len(fb_non_fb_url)}  ← should be 0 or very low")
    if fb_non_fb_url:
        print("  Sample non-FB URLs (first 3):")
        for d in fb_non_fb_url[:3]:
            print(f"    {d['url'][:100]}")

    breakdown: dict = {}
    for d in all_docs:
        breakdown[d["source_zip"]] = breakdown.get(d["source_zip"], 0) + 1
    print("\nSource breakdown:")
    for k, v in sorted(breakdown.items()):
        print(f"  {k}: {v}")

    print("\nStep 3: Building FAISS index…")
    build_index(all_docs, OUTPUT_DIR)

    print("\n" + "=" * 60)
    print(f"  DONE — {len(all_docs)} documents indexed")
    print("=" * 60)
    print(f"\nOutput: {OUTPUT_DIR}")
    print("\nNext: copy faiss_index.bin + faiss_metadata.pkl to")
    print("      backend/data/vector_databases/main_index/ and redeploy Koyeb.")

if __name__ == "__main__":
    main()