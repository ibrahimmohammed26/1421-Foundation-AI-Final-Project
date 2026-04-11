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

# Which zip files to read
ZIP_FILES = [
        r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\1421FacebookWebsite\facebook_pages_csv.zip",
        r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\1421FacebookWebsite\facebook_posts.zip",
        r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\1421FoundationWebsite\1421_foundation_scraped.zip",
        r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\GavinMenziesWebsite\1421_evidence_scraped.zip",
        r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\GavinMenziesWebsite\1434_evidence_scraped.zip",
        r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\GavinMenziesWebsite\america_evidence_scraped.zip",
        r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\GavinMenziesWebsite\atlantis_evidence_scraped.zip",
        r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\GavinMenziesWebsite\gavin_menzies_scraped.zip",
        r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\3BooksAndMore\pdf_evidence_scraped.zip"
    ]

# Where to save the output
OUTPUT_DIR = Path(r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\data\vector_databases\main_index")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
BOOK_ZIP_NAME = "pdf_evidence_scraped.zip"

# Facebook pages we don't want to index
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
    if not url:
        return False
    url_clean = url.strip().rstrip("/")
    for ex in EXCLUDED_URLS:
        if url_clean == ex.rstrip("/"):
            return True
    return False


def clean_url(raw):
    s = (raw or "").strip()
    if s.startswith(("http://", "https://")):
        return s
    return ""


def is_fb_posts(zip_name):
    return "facebook_posts" in zip_name.lower()


def is_fb_pages(zip_name):
    return "facebook" in zip_name.lower() and "page" in zip_name.lower()


def is_fb_any(zip_name):
    return "facebook" in zip_name.lower()


def is_links_csv(filename):
    return filename.lower().endswith("_links.csv")


def get_default_author(zip_name):
    z = zip_name.lower()
    if "facebook" in z:
        return "1421 Foundation (Facebook)"
    if "1421_foundation" in z:
        return "1421 Foundation (Website)"
    return "Gavin Menzies"


def get_column_map(cols):
    result = {}
    for c in cols:
        result[str(c).lower()] = c
    return result


def pick_url_column(cols, zip_name, csv_filename):
    """
    Which column has the URL? Depends on what kind of file we're reading.
    """
    col_map = get_column_map(cols)
    fname_lower = csv_filename.lower()


    # For _links.csv files (external articles linked from Facebook posts)
    if is_links_csv(fname_lower):
        for col_name in ["link_url", "url", "link", "source_url"]:
            if col_name in col_map:
                return col_map[col_name], f"link article url ({col_map[col_name]})"
        return None, "NONE — no url col in links csv"

    # For Facebook posts main CSV files
    if is_fb_posts(zip_name):
        for col_name in ["post_url", "permalink", "post_link"]:
            if col_name in col_map:
                return col_map[col_name], f"post permalink ({col_map[col_name]})"
        return None, "NONE — no post_url"

    # For Facebook pages CSV files
    if is_fb_pages(zip_name):
        for col_name in ["page_url", "source_url", "url", "link"]:
            if col_name in col_map:
                return col_map[col_name], f"page url ({col_map[col_name]})"
        for col in cols:
            if "url" in str(col).lower():
                return col, f"url fallback ({col})"
        return None, "NONE"

    # For everything else (books, evidence pages, etc.)
    for col_name in ["source_url", "document_url", "url", "link", "page_url", "post_url"]:
        if col_name in col_map:
            return col_map[col_name], f"standard ({col_map[col_name]})"
    
    for col in cols:
        if "url" in str(col).lower():
            return col, f"url fallback ({col})"
    
    return None, "NONE"


def find_column(cols, *keywords):
    col_map = get_column_map(cols)
    for kw in keywords:
        if kw in col_map:
            return col_map[kw]
    for kw in keywords:
        for col in cols:
            if kw in str(col).lower():
                return col
    return None



def get_value(row, col):
    if col is None:
        return ""
    val = row.get(col, "")
    if pd.isna(val):
        return ""
    return str(val).strip()


def remove_urls(text):
    cleaned = URL_RE.sub("", text or "")
    cleaned = re.sub(r'\s*[:|]\s*$', '', cleaned)
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)
    return cleaned.strip().rstrip(".,;:-\u2013\u2014")


def clean_title(raw):
    if not raw:
        return ""
    
    t = remove_urls(raw.strip())
    if not t:
        return ""
    
    # Remove duplicate halves if present
    half_len = len(t) // 2
    if half_len > 10 and t[:half_len] == t[half_len:]:
        t = t[:half_len].strip()
    
    words = t.split()
    mid = len(words) // 2
    if mid > 0 and words[:mid] == words[mid:]:
        t = " ".join(words[:mid]).strip()
    # Skip if it's just an author name
    author_patterns = [
        "Gavin Menzies", "1421 Foundation", "The 1421 Foundation",
        "1421 Foundation (Facebook)", "1421 Foundation (Website)"
    ]
    for pattern in author_patterns:
        if re.fullmatch(pattern, t, re.IGNORECASE):
            return ""
    
    t = t.strip(".,;:-\u2013\u2014")
    return t[:400] if t else ""


def extract_title_from_content(content, fallback):
    if not content or not content.strip():
        return fallback[:400]
    
    # Remove common prefix patterns
    text = re.sub(
        r"^(Title|Author|Content|Source|Type|Tags)\s*:\s*",
        "", content.strip(), flags=re.IGNORECASE
    ).strip()
    
    if not text:
        return fallback[:400]
    
    # Take first sentence
    parts = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)
    first = parts[0].strip()
    
    if len(first) < 15:
        first = text[:200].strip()
    elif len(first) > 300:
        first = first[:300].strip()
    

    first = remove_urls(first).rstrip(".,;:")
    
    if not first or len(first) < 5:
        return fallback[:400]
    
    return first[:400]


def read_csv_from_zip(zip_ref, csv_filename):
    for encoding in ["utf-8-sig", "utf-8", "latin-1"]:
        try:
            with zip_ref.open(csv_filename) as f:
                return pd.read_csv(f, encoding=encoding)
        except Exception:
            continue
    return None


def process_csv(df, csv_filename, zip_name, seen_titles):
    """
    seen_titles: keeps track of titles we've already seen within this zip file
    """
    docs = []
    
    if df is None or len(df) == 0:
        return docs
    
    cols = list(df.columns)
    is_book = (zip_name == BOOK_ZIP_NAME)
    is_fb = is_fb_any(zip_name)
    is_links = is_links_csv(csv_filename)
    
    # Find the right columns
    content_col = find_column(cols,
        "full_content", "content", "post_content", "page_content",
        "link_content", "text", "body", "section")
    
    title_col = find_column(cols,
        "title", "document_title", "name", "post_title", "page_title",
        "link_title")
    
    author_col = find_column(cols,
        "author", "posted_by", "creator", "post_author")
    
    page_col = find_column(cols, "page_number", "page")
    
    url_col, url_desc = pick_url_column(cols, zip_name, csv_filename)
    
    default_author = get_default_author(zip_name)
    
    # Print debug info for Facebook and book files
    if is_fb or is_book:
        if is_book:
            tag = "[BOOKS]"
        elif is_links:
            tag = "[FB-LINKS]"
        elif is_fb_posts(zip_name):
            tag = "[FB-POSTS]"
        else:
            tag = "[FB-PAGES]"
        
        print(f"      {tag} {Path(csv_filename).name}")
        print(f"        cols: {cols}")
        print(f"        content={content_col} | title={title_col} | url={url_desc}")
    

    skipped = {"no_url": 0, "excluded": 0, "dup": 0}
    
    for idx, row in df.iterrows():
        content = get_value(row, content_col)
        url = clean_url(get_value(row, url_col))
        
        # Need a URL to index
        if not url:
            skipped["no_url"] += 1
            continue
        
        # Skip Facebook navigation pages
        if is_excluded_url(url):
            skipped["excluded"] += 1
            continue
        
        # Figure out author
        raw_author = get_value(row, author_col)
        if raw_author and len(raw_author) > 1:
            cleaned_author = clean_title(raw_author)
            if cleaned_author:
                author = cleaned_author
            else:
                author = default_author
        else:
            author = default_author
        
        # Figure out title
        raw_title = get_value(row, title_col)
        cleaned = clean_title(raw_title)
        

        # Skip titles that are too long or have "Evidence" in them
        if len(cleaned) > 300 or (len(cleaned.split()) > 40 and "Evidence" in cleaned):
            cleaned = ""
        
        if cleaned:
            title = cleaned
        else:
            fallback = f"Document from {Path(csv_filename).stem}"
            title = extract_title_from_content(content, fallback)
        
        # Create a deduplication key
        if is_book:
            page_num = get_value(row, page_col)
            dedup_key = f"{title.strip().lower()}|||page={page_num}"
        elif is_links:
            dedup_key = url
        else:
            dedup_key = title.strip().lower()
        
        # Check if we've seen this document already in this zip
        if dedup_key and dedup_key in seen_titles:
            skipped["dup"] += 1
            continue
        
        if dedup_key:
            seen_titles.add(dedup_key)
        
        # Prepare the content text
        content_text = content if content else f"Source: {url}"
        
        docs.append({
            "title": title,
            "url": url[:500],
            "author": author[:200],
            "source_type": "book" if is_book else "web",
            "source_file": Path(csv_filename).name,
            "source_zip": zip_name,
            "content_text": content_text,
            "row_index": idx,
        })
    
    print(f"        kept={len(docs)} | no_url={skipped['no_url']} | "
          f"excluded={skipped['excluded']} | dup={skipped['dup']}")
    
    return docs


def process_zip_file(zip_path):
    docs = []
    if not Path(zip_path).exists():
        print(f"  WARNING: ZIP not found — {Path(zip_path).name}")
        print(f"  Full path: {zip_path}")
        return docs
    
    zip_name = Path(zip_path).name
    print(f"\n  Processing {zip_name}...")
    
    seen_titles = set()
    
    with zipfile.ZipFile(zip_path, "r") as zf:
        # Find all CSV files (skip summary/error files)
        csv_files = []
        for f in zf.namelist():
            if f.lower().endswith(".csv"):
                skip = False
                for skip_word in ["summary", "error", "mapping", "log", "all_books"]:
                    if skip_word in f.lower():
                        skip = True
                        break
                if not skip:
                    csv_files.append(f)
        
        print(f"    {len(csv_files)} CSV file(s)")
        
        for csv_file in csv_files:
            df = read_csv_from_zip(zf, csv_file)
            if df is not None and len(df) > 0:
                file_docs = process_csv(df, csv_file, zip_name, seen_titles)
                docs.extend(file_docs)
    
    print(f"    Total from {zip_name}: {len(docs)}")
    return docs


def deduplicate_by_url(documents):
    seen_urls = set()
    unique = []
    dup_count = 0
    
    for doc in documents:
        # Books are already deduplicated by title+page, skip URL dedup for them
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


def build_faiss_index(documents, output_dir):
    print(f"\n  Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    
    raw_texts = []
    metadatas = []
    embed_texts = []
    
    for doc in documents:
        raw_texts.append(doc["content_text"])
        metadatas.append({
            "title": doc["title"],
            "url": doc["url"],
            "author": doc["author"],
            "source_type": doc["source_type"],
            "source_file": doc["source_file"],
            "year": 0,
            "tags": [],
            "page": None,
        })
        embed_texts.append(
            f"Title: {doc['title']} Author: {doc['author']} Content: {doc['content_text'][:500]}"
        )
    

    print(f"  Creating embeddings for {len(embed_texts)} documents...")
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
    
    # Save FAISS index
    faiss.write_index(index, str(output_dir / "faiss_index.bin"))
    print(f"  Saved FAISS index  -> {output_dir / 'faiss_index.bin'}")
    
    # Save metadata
    with open(output_dir / "faiss_metadata.pkl", "wb") as f:
        pickle.dump({"documents": raw_texts, "metadatas": metadatas}, f)
    print(f"  Saved metadata     -> {output_dir / 'faiss_metadata.pkl'}")
    
    # Save statistics
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
    print("  REBUILD INDEX")
    print("=" * 60)
    
    all_docs = []
    
    print("\nStep 1: Reading ZIP files...")
    for zip_path in ZIP_FILES:
        docs = process_zip_file(zip_path)
        all_docs.extend(docs)
        print(f"  Running total: {len(all_docs)}")
    
    print(f"\nTotal before URL dedup: {len(all_docs)}")
    
    print("\nStep 2: Global URL deduplication...")
    all_docs = deduplicate_by_url(all_docs)
    print(f"Total after URL dedup:  {len(all_docs)}")
    
    # Print some diagnostics
    by_author = {}
    for d in all_docs:
        by_author[d["author"]] = by_author.get(d["author"], 0) + 1
    
    print("\nAuthor breakdown:")
    for author_name, count in sorted(by_author.items()):
        print(f"  {author_name}: {count}")
    
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
    for zip_name, count in sorted(breakdown.items()):
        print(f"  {zip_name}: {count}")
    print("\nStep 3: Building FAISS index...")
    build_faiss_index(all_docs, OUTPUT_DIR)
    
    print("\n" + "=" * 60)
    print(f"  DONE — {len(all_docs)} documents indexed")
    print("=" * 60)
    print(f"\nOutput: {OUTPUT_DIR}")
    print("\nNext: copy faiss_index.bin + faiss_metadata.pkl to")
    print("      backend/data/vector_databases/main_index/ and redeploy Koyeb.")


if __name__ == "__main__":
    main()