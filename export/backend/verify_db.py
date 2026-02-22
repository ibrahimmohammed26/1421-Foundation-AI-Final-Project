"""
verify_db.py — Run this from your backend folder:
    python verify_db.py

It checks your SQLite database, vector files, and prints exactly what
the /api/documents endpoint will see.
"""

import sqlite3
import pickle
import json
from pathlib import Path

DIVIDER = "─" * 60

def section(title):
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)

# ── 1. File existence ────────────────────────────────────────────────

section("1. FILE EXISTENCE")

files = {
    "SQLite DB":         Path(__file__).resolve().parents[2] / "data" / "knowledge_base.db",
    "FAISS index":       Path(__file__).resolve().parents[2] / "data" / "vector_databases" / "main_index" / "faiss_index.bin",
    "FAISS metadata":    Path(__file__).resolve().parents[2] / "data" / "vector_databases" / "main_index" / "faiss_metadata.pkl",
    "DB stats JSON":     Path(__file__).resolve().parents[2] / "data" / "database_stats.json",
}

for label, path in files.items():
    exists = path.exists()
    size   = f"{path.stat().st_size / 1024:.1f} KB" if exists else "—"
    status = "✅" if exists else "❌ MISSING"
    print(f"  {status}  {label:20s}  {path}  ({size})")

# ── 2. SQLite inspection ─────────────────────────────────────────────

section("2. SQLITE DATABASE")

db_path = Path(__file__).resolve().parents[2] / "data" / "knowledge_base.db"
if not db_path.exists():
    print("  ❌ knowledge_base.db not found — skipping SQLite checks")
else:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print(f"  Tables found: {tables}")

    if "documents" not in tables:
        print("  ❌ 'documents' table is MISSING — this is why the page shows nothing!")
        print("     You need to run your indexer/ingest script to populate it.")
    else:
        # Count
        cur.execute("SELECT COUNT(*) FROM documents")
        total = cur.fetchone()[0]
        print(f"  Total rows in documents: {total}")

        if total == 0:
            print("  ❌ Table exists but is EMPTY — run your indexer to populate it.")
        else:
            # Columns
            cur.execute("PRAGMA table_info(documents)")
            cols = [r["name"] for r in cur.fetchall()]
            print(f"  Columns: {cols}")

            # Sample rows
            cur.execute("SELECT * FROM documents LIMIT 3")
            rows = cur.fetchall()
            print(f"\n  Sample documents (first 3):")
            for row in rows:
                d = dict(row)
                # Truncate long fields for readability
                for k in ["content_preview", "description", "content"]:
                    if k in d and d[k] and len(str(d[k])) > 80:
                        d[k] = str(d[k])[:80] + "..."
                print(f"    id={d.get('id')}  title={d.get('title')}  year={d.get('year')}  type={d.get('type')}")

            # Year distribution
            cur.execute("SELECT year, COUNT(*) as n FROM documents GROUP BY year ORDER BY year DESC LIMIT 10")
            years = cur.fetchall()
            print(f"\n  Year distribution (top 10):")
            for y in years:
                print(f"    {y['year'] or 'NULL':>6}  →  {y['n']} docs")

            # Type distribution
            cur.execute("SELECT type, COUNT(*) as n FROM documents GROUP BY type ORDER BY n DESC")
            types = cur.fetchall()
            print(f"\n  Type distribution:")
            for t in types:
                print(f"    {str(t['type'] or 'NULL'):>20}  →  {t['n']} docs")

            # Null/empty title check
            cur.execute("SELECT COUNT(*) FROM documents WHERE title IS NULL OR title = ''")
            null_titles = cur.fetchone()[0]
            if null_titles:
                print(f"\n  ⚠️  {null_titles} documents have NULL or empty titles")

    conn.close()

# ── 3. Vector database inspection ────────────────────────────────────

section("3. VECTOR DATABASE (FAISS metadata)")

meta_path = Path(__file__).resolve().parents[2] / "data" / "vector_databases" / "main_index" / "faiss_metadata.pkl"
if not meta_path.exists():
    print("  ❌ faiss_metadata.pkl not found — skipping")
else:
    with open(meta_path, "rb") as f:
        data = pickle.load(f)

    print(f"  Top-level keys in pickle: {list(data.keys()) if isinstance(data, dict) else type(data)}")

    if isinstance(data, dict):
        for key in ["documents", "metadatas", "document_ids", "embeddings"]:
            val = data.get(key)
            if val is not None:
                print(f"  '{key}': {type(val).__name__} with {len(val)} entries")
            else:
                print(f"  '{key}': not present")

        # Sample metadata
        metas = data.get("metadatas", [])
        if metas:
            print(f"\n  Sample metadata (first 3):")
            for m in metas[:3]:
                print(f"    {m}")

        # Check if metadata uses str(idx) keys (old format)
        non_list_keys = [k for k in data.keys() if k not in ["documents","metadatas","document_ids","embeddings"]]
        if non_list_keys:
            print(f"\n  Other keys (may be str-indexed): {non_list_keys[:10]}")
            sample_key = non_list_keys[0]
            print(f"  Sample entry for key '{sample_key}': {data[sample_key]}")
    else:
        print(f"  Pickle contains a {type(data).__name__}, not a dict — metadata format may differ")

# ── 4. FAISS index ───────────────────────────────────────────────────

section("4. FAISS INDEX")

faiss_path = Path(__file__).resolve().parents[2] / "data" / "vector_databases" / "main_index" / "faiss_index.bin"
if not faiss_path.exists():
    print("  ❌ faiss_index.bin not found")
else:
    try:
        import faiss
        index = faiss.read_index(str(faiss_path))
        print(f"  ✅ Loaded FAISS index")
        print(f"     Vectors stored: {index.ntotal}")
        print(f"     Dimensions:     {index.d}")
    except ImportError:
        print("  ⚠️  faiss not installed — cannot inspect index (pip install faiss-cpu)")
    except Exception as e:
        print(f"  ❌ Error reading FAISS index: {e}")

# ── 5. Simulate the /api/documents endpoint ──────────────────────────

section("5. SIMULATING /api/documents?limit=50&offset=0")

db_path = Path(__file__).resolve().parents[2] / "data" / "knowledge_base.db"
if db_path.exists():
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
        if not cur.fetchone():
            print("  ❌ 'documents' table missing — endpoint will return []")
        else:
            cur.execute("SELECT COUNT(*) FROM documents")
            total = cur.fetchone()[0]

            cur.execute("PRAGMA table_info(documents)")
            available = {r["name"] for r in cur.fetchall()}
            select_cols = [c for c in ["id","title","author","year","type","description",
                                        "tags","content_preview","source_file","page_number"]
                           if c in available]
            col_str = ", ".join(select_cols)

            cur.execute(f"SELECT {col_str} FROM documents ORDER BY year DESC LIMIT 50 OFFSET 0")
            rows = cur.fetchall()
            print(f"  Would return {len(rows)} documents (total={total})")
            if rows:
                print(f"  First result: id={dict(rows[0]).get('id')}  title={dict(rows[0]).get('title')}")
            else:
                print("  ❌ Query returned 0 rows even though COUNT(*) says otherwise — check permissions")
        conn.close()
    except Exception as e:
        print(f"  ❌ Simulation error: {e}")
else:
    print("  ❌ Database file not found")

# ── 6. Summary & recommendations ────────────────────────────────────

section("6. SUMMARY & NEXT STEPS")

issues = []

if not Path(__file__).resolve().parents[2] / "data" / "knowledge_base.db".exists():
    issues.append("knowledge_base.db is missing — run your data ingestion/indexer script")
else:
    conn = sqlite3.connect(str(Path(__file__).resolve().parents[2] / "data" / "knowledge_base.db"))
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
    if not cur.fetchone():
        issues.append("'documents' table doesn't exist in knowledge_base.db")
    else:
        cur.execute("SELECT COUNT(*) FROM documents")
        n = cur.fetchone()[0]
        if n == 0:
            issues.append("'documents' table is empty — run your indexer to populate it")
        else:
            print(f"  ✅ SQLite looks good — {n} documents ready to serve")
    conn.close()

if not Path(__file__).resolve().parents[2] / "data" / "vector_databases" / "main_index" / "faiss_index.bin".exists():
    issues.append("faiss_index.bin missing — semantic search won't work (keyword search will still work)")

if issues:
    print("\n  ❌ Issues found:")
    for i, issue in enumerate(issues, 1):
        print(f"     {i}. {issue}")
else:
    print("  ✅ Everything looks healthy — check CORS or the API URL in your frontend .env")
    print("     Try visiting http://localhost:8000/api/documents in your browser to confirm the API works")