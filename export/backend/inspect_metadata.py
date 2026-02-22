"""
inspect_metadata.py — Run from your backend folder:
    python inspect_metadata.py

Shows the exact structure of your FAISS metadata so we can fix the ID lookup.
"""
import pickle
import sqlite3
from pathlib import Path

BASE_DIR  = Path(__file__).resolve().parents[2]
META_PATH = BASE_DIR / "data" / "vector_databases" / "main_index" / "faiss_metadata.pkl"
DB_PATH   = BASE_DIR / "data" / "knowledge_base.db"

print(f"Loading: {META_PATH}")
with open(META_PATH, "rb") as f:
    data = pickle.load(f)

print(f"\nType of pickle contents: {type(data)}")

if isinstance(data, dict):
    print(f"Top-level keys ({len(data)} total): {list(data.keys())[:15]}")
    print()

    # Show value type for each key
    for key in list(data.keys())[:5]:
        val = data[key]
        print(f"  key={repr(key)}  type={type(val).__name__}  ", end="")
        if isinstance(val, (list, dict)):
            print(f"len={len(val)}")
            if isinstance(val, list) and val:
                print(f"    first item: {repr(val[0])[:120]}")
            elif isinstance(val, dict):
                sub_keys = list(val.keys())[:5]
                print(f"    sub-keys: {sub_keys}")
                for sk in sub_keys[:2]:
                    print(f"      [{repr(sk)}] = {repr(val[sk])[:100]}")
        else:
            print(f"value={repr(val)[:80]}")

elif isinstance(data, list):
    print(f"List with {len(data)} items")
    print(f"First item: {repr(data[0])[:200]}")
    print(f"Second item: {repr(data[1])[:200]}")

print("\n" + "="*60)
print("CHECKING: What does index 0 resolve to?")

# Try all known formats
idx = 0

if isinstance(data, dict):
    # Format 1: str key
    if str(idx) in data:
        entry = data[str(idx)]
        print(f"Format 1 (str key): data['0'] = {repr(entry)[:150]}")
        if isinstance(entry, dict):
            print(f"  -> id field = {repr(entry.get('id', 'NOT FOUND'))}")

    # Format 2: lists
    doc_ids = data.get("document_ids", [])
    metas   = data.get("metadatas", [])
    docs    = data.get("documents", [])
    if doc_ids:
        print(f"Format 2 (document_ids list): doc_ids[0] = {repr(doc_ids[0])[:100]}")
    if metas:
        print(f"Format 2 (metadatas list): metadatas[0] = {repr(metas[0])[:150]}")
    if docs:
        print(f"Format 2 (documents list): documents[0] = {repr(docs[0])[:100]}")

print("\n" + "="*60)
print("CHECKING: SQLite document IDs (first 5)")

conn = sqlite3.connect(str(DB_PATH))
rows = conn.execute("SELECT id, title FROM documents LIMIT 5").fetchall()
for row in rows:
    print(f"  SQLite id={repr(row[0])}  title={row[1][:60]}")
conn.close()

print("\n" + "="*60)
print("DIAGNOSIS: Do FAISS metadata IDs match SQLite IDs?")
print("Compare the id values above - they must match exactly for RAG to work.")