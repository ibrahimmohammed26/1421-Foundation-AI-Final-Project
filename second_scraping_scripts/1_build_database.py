"""
Builds the SQLite database in the data folder, using the scraped csv files
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
from tqdm import tqdm
import warnings

warnings.filterwarnings("ignore")


# =========================================================
# Simple entity extraction (regex only)
# =========================================================
class SimpleEntityExtractor:
    def __init__(self):
        # These are just practical patterns
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
                r"\b(\d{4})\s*[-–]\s*(\d{4})\b",
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
                    if match.groups():
                        value = match.group(1) or match.group()
                    else:
                        value = match.group()

                    if len(value.strip()) < 2:
                        continue

                    entities.append({
                        "text": value,
                        "type": entity_type,
                        "start": match.start(),
                        "end": match.end(),
                        "confidence": 0.8,
                    })

        # dedupe (basic)
        seen = set()
        unique = []
        for e in entities:
            key = (e["text"], e["start"], e["type"])
            if key not in seen:
                seen.add(key)
                unique.append(e)

        return unique

    def extract_dates(self, text):
        dates = []
        pattern = r"\b(1[3-9]\d{2}|20[0-2]\d)\b"

        for m in re.finditer(pattern, text):
            year = int(m.group())

            start = max(0, m.start() - 50)
            end = min(len(text), m.end() + 100)

            context = text[start:end]
            context = re.sub(r"\s+", " ", context).strip()

            dates.append({
                "year": year,
                "text": str(year),
                "context": context[:200],
            })

        return dates


# =========================================================
# Database
# =========================================================
class DatabaseManager:
    def __init__(self, db_path="data/knowledge_base.db"):
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
            INSERT INTO entities (doc_id, entity_text, entity_type, start_pos, end_pos, confidence)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                doc_id,
                e["text"][:200],
                e["type"],
                e["start"],
                e["end"],
                e["confidence"],
            ))

        self.conn.commit()
        return doc_id

    def get_stats(self):
        c = self.conn.cursor()


        total_docs = c.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        total_entities = c.execute("SELECT COUNT(*) FROM entities").fetchone()[0]

        return {
            "total_documents": total_docs,
            "total_entities": total_entities,
        }


# =========================================================
# Vector DB
# =========================================================

class VectorDatabaseCreator:
    def __init__(self, db):
        self.db = db
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.base = Path("vector_databases")
        self.base.mkdir(exist_ok=True)

    def create_vector_database(self):
        c = self.db.conn.cursor()
        rows = c.execute(
            "SELECT id, title, content FROM documents WHERE LENGTH(content) > 100"
        ).fetchall()

        if not rows:
            print("No docs to embed")
            return

        docs = []
        meta = []

        for r in rows:
            doc_id, title, content = r
            text = f"{title or 'Untitled'}\n{content}"
            docs.append(text)
            meta.append({"id": doc_id})

        print("Embedding... this might take a bit")

        embeddings = self.model.encode(
            docs,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")

        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)

        out = self.base / "main_index"
        out.mkdir(exist_ok=True)

        faiss.write_index(index, str(out / "faiss_index.bin"))

        with open(out / "faiss_metadata.pkl", "wb") as f:
            pickle.dump(meta, f)

        print(f"Saved {len(docs)} vectors")



# =========================================================
# Processing
# =========================================================

def process_zip(zip_path, db, extractor):
    zip_path = Path("data") / zip_path  # will be saved in the data folder

    if not zip_path.exists():
        print(f"Missing: {zip_path}")
        return 0

    count = 0

    with zipfile.ZipFile(zip_path, "r") as z:
        csvs = [f for f in z.namelist() if f.endswith(".csv")]

        for name in csvs[:50]:
            with z.open(name) as f:
                try:
                    df = pd.read_csv(f)
                except:
                    f.seek(0)
                    df = pd.read_csv(f, encoding="latin-1")

            for _, row in df.iterrows():
                content = str(row.get("content", ""))
                if len(content) < 50:
                    continue

                entities = extractor.extract_entities(content)

                doc = {
                    "source_type": "general",
                    "source_file": name,
                    "title": str(row.get("title", "")),
                    "content": content,
                    "url": str(row.get("url", "")),
                    "author": str(row.get("author", "")),
                    "word_count": len(content.split()),
                    "source_zip": zip_path.name,
                    "content_length": len(content),
                    "entities": entities,
                }

                db.insert_document(doc)
                count += 1

    return count

# =========================================================
# main
# =========================================================

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
        r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\scraped_csvs\3BooksAndMore\pdf_evidence_scraped.zip"
    ]

    extractor = SimpleEntityExtractor()
    db = DatabaseManager()

    db.create_tables()

    total = 0
    for z in ZIP_FILES:
        total += process_zip(z, db, extractor)

    print(f"Imported {total} docs")

    vec = VectorDatabaseCreator(db)
    vec.create_vector_database()

    stats = db.get_stats()
    print(stats)

if __name__ == "__main__":
    main()