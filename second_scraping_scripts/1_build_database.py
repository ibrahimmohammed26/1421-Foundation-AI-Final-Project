"""
build_database.py
Builds the SQLite knowledge base from all scraped ZIP files.
Output: data/knowledge_base.db  +  vector_databases/main_index/
"""

import os
import sys
import zipfile
import pandas as pd
import sqlite3
from pathlib import Path
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import json
from datetime import datetime
import re
import warnings

warnings.filterwarnings("ignore")


# ── Entity extraction (regex only) ───────────────────────────────────────────

class SimpleEntityExtractor:
    def __init__(self):
        self.patterns = {
            "PERSON": [
                r"\b(Zheng He|Hong Bao|Zhou Man|Kublai Khan|Emperor Yongle|Zhu Di)\b",
                r"\b(Gavin Menzies|Ian Hudson)\b",
                r"\b(Admiral [A-Z][a-z]+)\b",
                r"\b(Captain [A-Z][a-z]+)\b",
                r"\b(Marco Polo|Christopher Columbus|Vasco da Gama)\b",
            ],
            "LOCATION": [
                r"\b(China|Beijing|Nanjing|Shanghai|Quanzhou|Guangzhou)\b",
                r"\b(Malacca|Calicut|Hormuz|Mombasa|Zanzibar|Aden)\b",
                r"\b(India|Sri Lanka|Sumatra|Java|Borneo|Philippines)\b",
                r"\b(America|California|Peru|Mexico|Brazil|Chile)\b",
                r"\b(Pacific Ocean|Indian Ocean|South China Sea|Arabian Sea)\b",
                r"\b(Africa|Europe|Asia|Australia|Antarctica)\b",
            ],
            "SHIP": [
                r"\b(Treasure Ship|baochuan|great fleet|Ming fleet)\b",
                r"\b(Zheng He's fleet|Chinese fleet|naval fleet)\b",
                r"\b([A-Z][a-z]+\s+(?:Ship|Fleet|Junk|Vessel))\b",
            ],
            "DATE": [
                r"\b(1[3-9]\d{2}|20[0-2]\d)\b",
                r"\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)[,.]?\s+\d{4})\b",
                r"\b(\d{4})\s*[-\u2013]\s*(\d{4})\b",
                r"\b(\d+(?:st|nd|rd|th)?\s+century)\b",
            ],
            "BOOK": [
                r'"([^"]+)"',
                r"\b(1421: The Year China Discovered America)\b",
                r"\b(1434: The Year a Magnificent Chinese Fleet)\b",
                r"\b(Who Discovered America\?)\b",
                r"\b(The Lost Empire of Atlantis)\b",
            ],
            "ORGANIZATION": [
                r"\b(1421 Foundation|Ming Dynasty|Chinese Empire)\b",
                r"\b(Royal Geographical Society|Explorers Club)\b",
                r"\b(National Geographic|Smithsonian)\b",
            ],
        }

    def extract_entities(self, text):
        entities = []
        for entity_type, patterns in self.patterns.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    value = match.group(1) if match.groups() else match.group()
                    if len(value.strip()) < 2:
                        continue
                    entities.append({
                        "text":       value,
                        "type":       entity_type,
                        "start":      match.start(),
                        "end":        match.end(),
                        "confidence": 0.8,
                    })
        # Basic dedup
        seen, unique = set(), []
        for e in entities:
            key = (e["text"], e["start"], e["type"])
            if key not in seen:
                seen.add(key)
                unique.append(e)
        return unique


# ── Database ──────────────────────────────────────────────────────────────────

class DatabaseManager:
    def __init__(self, db_path="data/knowledge_base.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def create_tables(self):
        c = self.conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT,
                source_file TEXT,
                title TEXT,
                content TEXT,
                url TEXT,
                author TEXT,
                word_count INTEGER,
                source_zip TEXT,
                content_length INTEGER,
                book_title TEXT,
                import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER,
                entity_text TEXT,
                entity_type TEXT,
                start_pos INTEGER,
                end_pos INTEGER,
                confidence REAL
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_doc_source ON documents(source_type)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type)")
        self.conn.commit()
        print("Database ready")

    def insert_document(self, doc):
        c = self.conn.cursor()
        c.execute("""
            INSERT INTO documents
            (source_type, source_file, title, content, url, author,
             word_count, source_zip, content_length, book_title)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            doc.get("source_type"),
            doc.get("source_file"),
            doc.get("title", "")[:500],
            doc.get("content", ""),
            doc.get("url", "")[:500],
            doc.get("author", "")[:100],
            doc.get("word_count", 0),
            doc.get("source_zip", ""),
            doc.get("content_length", 0),
            doc.get("book_title", "")[:200],
        ))
        doc_id = c.lastrowid
        for e in doc.get("entities", []):
            c.execute("""
                INSERT INTO entities
                (doc_id, entity_text, entity_type, start_pos, end_pos, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (doc_id, e["text"][:200], e["type"], e["start"], e["end"], e["confidence"]))
        self.conn.commit()
        return doc_id

    def get_stats(self):
        c = self.conn.cursor()
        return {
            "total_documents": c.execute("SELECT COUNT(*) FROM documents").fetchone()[0],
            "total_entities":  c.execute("SELECT COUNT(*) FROM entities").fetchone()[0],
        }


# ── Vector DB ─────────────────────────────────────────────────────────────────

class VectorDatabaseCreator:
    def __init__(self, db):
        self.db   = db
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.base  = Path("data/vector_databases")
        self.base.mkdir(exist_ok=True)

    def create_vector_database(self):
        rows = self.db.conn.cursor().execute(
            "SELECT id, title, content FROM documents WHERE LENGTH(content) > 100"
        ).fetchall()

        if not rows:
            print("No documents to embed.")
            return

        docs, meta = [], []
        for doc_id, title, content in rows:
            docs.append(f"{title or 'Untitled'}\n{content}")
            meta.append({"id": doc_id})

        print(f"Embedding {len(docs)} documents...")
        embeddings = self.model.encode(
            docs,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        ).astype("float32")

        dim   = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)

        out = self.base / "main_index"
        out.mkdir(exist_ok=True)

        faiss.write_index(index, str(out / "faiss_index.bin"))
        with open(out / "faiss_metadata.pkl", "wb") as f:
            pickle.dump(meta, f)

        print(f"Saved {len(docs)} vectors to {out}")


# ── ZIP processing ────────────────────────────────────────────────────────────

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

def is_excluded(url):
    if not url:
        return False
    return url.strip().rstrip("/") in {u.rstrip("/") for u in EXCLUDED_URLS}

def valid_url(raw):
    s = (raw or "").strip()
    return s if s.startswith(("http://", "https://")) else ""


def process_zip(zip_path, db, extractor):
    zip_path = Path(zip_path)
    if not zip_path.exists():
        print(f"  Missing: {zip_path}")
        return 0

    zip_name = zip_path.name
    count = 0

    with zipfile.ZipFile(zip_path, "r") as z:
        # No [:50] cap — process ALL CSV files
        csv_files = [
            f for f in z.namelist()
            if f.lower().endswith(".csv")
            and not any(x in f.lower() for x in
                        ["summary", "error", "mapping", "log", "all_books"])
        ]

        print(f"  {zip_name}: {len(csv_files)} CSV file(s)")

        for name in csv_files:
            with z.open(name) as f:
                try:
                    df = pd.read_csv(f)
                except Exception:
                    try:
                        df = pd.read_csv(f, encoding="latin-1")
                    except Exception:
                        continue

            for _, row in df.iterrows():
                # Must have a valid URL
                url = valid_url(str(row.get("url", "") or row.get("source_url", "") or ""))
                if not url:
                    continue
                if is_excluded(url):
                    continue

                content = str(row.get("content", "") or
                              row.get("full_content", "") or
                              row.get("post_content", "") or "")
                if not content.strip():
                    continue

                entities = extractor.extract_entities(content)

                db.insert_document({
                    "source_type":    "general",
                    "source_file":    name,
                    "title":          str(row.get("title", "") or row.get("post_title", "") or ""),
                    "content":        content,
                    "url":            url,
                    "author":         str(row.get("author", "") or ""),
                    "word_count":     len(content.split()),
                    "source_zip":     zip_name,
                    "content_length": len(content),
                    "entities":       entities,
                })
                count += 1

    print(f"  -> {count} documents inserted from {zip_name}")
    return count


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Starting pipeline...")

    ZIP_FILES = [
        
        r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\1421FacebookWebsite\facebook_pages_csv.zip",
        r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\1421FacebookWebsite\facebook_posts.zip",
        r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\1421FoundationWebsite\1421_foundation_scraped.zip",
        r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\GavinMenziesWebsite\1421_evidence_scraped.zip",
        r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\GavinMenziesWebsite\1434_evidence_scraped.zip",
        r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\GavinMenziesWebsite\america_evidence_scraped.zip",
        r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\GavinMenziesWebsite\atlantis_evidence_scraped.zip",
        r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\GavinMenziesWebsite\gavin_menzies_scraped.zip",
        r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\BooksAndMore\pdf_evidence_scraped.zip",
    ]
    extractor = SimpleEntityExtractor()
    db        = DatabaseManager()
    db.create_tables()
    total = 0
    for z in ZIP_FILES:
        total += process_zip(z, db, extractor)

    print(f"\nTotal documents inserted: {total}")

    vec = VectorDatabaseCreator(db)
    vec.create_vector_database()

    print(db.get_stats())


if __name__ == "__main__":
    main()