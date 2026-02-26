"""
diagnose.py — Run this from your backend folder to find exactly what's broken.

Usage:
    cd C:\\Users\\ibrah\\1421-Foundation-AI-Final-Project\\backend
    C:\\Users\\ibrah\\1421-Foundation-AI-Final-Project\\venv\\Scripts\\python.exe diagnose.py
"""

import json
import sys
import os
import urllib.request
import urllib.error
from pathlib import Path

BASE_URL = "http://localhost:8000"
LINE = "=" * 60


def get(path, timeout=15):
    try:
        with urllib.request.urlopen(f"{BASE_URL}{path}", timeout=timeout) as r:
            return r.status, json.loads(r.read()), None
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read())
        except Exception:
            body = {}
        return e.code, body, str(e)
    except Exception as e:
        return 0, None, str(e)


def post(path, body, timeout=30):
    try:
        payload = json.dumps(body).encode()
        req = urllib.request.Request(
            f"{BASE_URL}{path}", data=payload,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read()), None
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read())
        except Exception:
            body = {}
        return e.code, body, str(e)
    except Exception as e:
        return 0, None, str(e)


print(f"\n{LINE}")
print("  1421 FOUNDATION — FULL DIAGNOSTIC")
print(LINE)

# ── 1. Server health ──────────────────────────────────────────────────
print("\n[1] Server health")
code, data, err = get("/")
if code != 200:
    print(f"  FAIL  Server not reachable: {err}")
    print("        Start with: python -m uvicorn main:app --reload")
    sys.exit(1)

docs_loaded = data.get("docs_loaded", 0)
print(f"  OK    Server running")
print(f"  INFO  docs_loaded = {docs_loaded}")
if docs_loaded == 0:
    print("  WARN  docs_loaded is 0 — documents not loading from pickle!")

# ── 2. Documents endpoint ─────────────────────────────────────────────
print("\n[2] Documents API")
code, data, err = get("/api/documents?limit=5")
if code != 200:
    print(f"  FAIL  GET /api/documents returned HTTP {code}: {err}")
else:
    total = data.get("total", 0)
    docs  = data.get("documents", [])
    print(f"  {'OK  ' if total > 0 else 'FAIL'}  total={total}, returned={len(docs)}")
    if total == 0:
        print("  CAUSE _docs_store is empty — pickle not loaded")
        print("        Check BASE_DIR in main.py and that the pickle file exists")
    elif docs:
        print(f"  INFO  First doc: {docs[0].get('title', 'NO TITLE')[:60]}")

# ── 3. Check pickle file directly ────────────────────────────────────
print("\n[3] Pickle file check (direct filesystem)")

# Try to figure out where main.py thinks BASE_DIR is
code2, data2, _ = get("/api/test-db")
if code2 == 200:
    store = data2.get("store_size", 0)
    faiss = data2.get("faiss_loaded", False)
    vecs  = data2.get("faiss_vectors", 0)
    sample = data2.get("sample", [])
    print(f"  INFO  store_size={store}, faiss_loaded={faiss}, faiss_vectors={vecs}")
    if sample:
        print(f"  INFO  Sample titles:")
        for s in sample:
            print(f"        - {s.get('title','?')[:60]}")
    if store == 0:
        print("  FAIL  Store is empty — check BASE_DIR and pickle path")

# Check common pickle locations
candidates = [
    Path(r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\data\vector_databases\main_index\faiss_metadata.pkl"),
    Path(r"C:\Users\ibrah\data\vector_databases\main_index\faiss_metadata.pkl"),
    Path(r"C:\Users\ibrah\1421-Foundation-AI-Final-Project\export\data\vector_databases\main_index\faiss_metadata.pkl"),
]
print("\n  Checking known pickle locations:")
for p in candidates:
    exists = p.exists()
    size   = f"{p.stat().st_size // 1024}KB" if exists else "—"
    print(f"  {'FOUND' if exists else 'MISS '} {p}  ({size})")

# ── 4. RAG debug ──────────────────────────────────────────────────────
print("\n[4] RAG context retrieval")
code, data, err = get("/api/debug/rag?q=Zheng+He")
if code != 200:
    print(f"  FAIL  /api/debug/rag returned HTTP {code}: {err}")
else:
    found   = data.get("docs_found", 0)
    faiss   = data.get("faiss_loaded", False)
    store   = data.get("store_size", 0)
    preview = data.get("context_preview", "")
    print(f"  INFO  docs_found={found}, faiss_loaded={faiss}, store_size={store}")
    if found == 0:
        print("  FAIL  RAG found 0 documents — LLM will answer from general knowledge only")
        if store == 0:
            print("  CAUSE store is empty (pickle not loaded)")
        elif not faiss:
            print("  CAUSE FAISS index not loaded (keyword search should still work)")
    else:
        print(f"  OK    RAG context: {preview[:200]}...")

# ── 5. Stats (Analytics) ──────────────────────────────────────────────
print("\n[5] Stats / Analytics endpoint")
code, data, err = get("/api/stats")
if code != 200:
    print(f"  FAIL  GET /api/stats returned HTTP {code}: {err}")
else:
    print(f"  OK    documents_count={data.get('documents_count')}, "
          f"locations_count={data.get('locations_count')}, "
          f"feedback_count={data.get('feedback_count')}")
    if data.get("documents_count", 0) == 0:
        print("  WARN  documents_count is 0 — Analytics will show empty charts")

# ── 6. Chat (non-streaming) ───────────────────────────────────────────
print("\n[6] Chat endpoint (non-streaming)")
code, data, err = post("/api/chat", {
    "messages": [{"role": "user", "content": "In one sentence, who was Zheng He?"}],
    "use_documents": True
}, timeout=45)
if code != 200:
    print(f"  FAIL  POST /api/chat returned HTTP {code}")
    if data:
        detail = data.get("detail", str(data))
        print(f"  ERROR {detail[:300]}")
    if "401" in str(err) or "invalid_api_key" in str(data):
        print("  CAUSE Invalid OpenAI API key")
        print("        Update OPENAI_API_KEY in backend/.env")
    elif "quota" in str(data).lower() or "billing" in str(data).lower():
        print("  CAUSE OpenAI account has no credits")
        print("        Add billing at https://platform.openai.com/account/billing")
else:
    content = data.get("content", "")
    sources = data.get("sources") or []
    print(f"  OK    Response received ({len(content)} chars)")
    print(f"  INFO  Sources: {len(sources)}")
    print(f"  INFO  Preview: {content[:150]}...")

# ── 7. Chat streaming ─────────────────────────────────────────────────
print("\n[7] Chat streaming endpoint")
try:
    import urllib.request
    payload = json.dumps({
        "messages": [{"role": "user", "content": "Say hello in 5 words."}],
        "use_documents": False
    }).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/api/chat/stream", data=payload,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    chunks = 0
    done   = False
    text   = ""
    with urllib.request.urlopen(req, timeout=30) as r:
        buf = b""
        while True:
            part = r.read(512)
            if not part:
                break
            buf += part
            while b"\n\n" in buf:
                line, buf = buf.split(b"\n\n", 1)
                line = line.strip()
                if line.startswith(b"data: "):
                    d = line[6:].decode("utf-8", errors="replace")
                    if d == "[DONE]":
                        done = True
                        break
                    if d.startswith("ERROR:"):
                        print(f"  FAIL  Stream error: {d}")
                        done = True
                        break
                    text += d.replace("\\n", "\n")
                    chunks += 1
            if done:
                break
    print(f"  {'OK  ' if chunks > 0 else 'FAIL'}  chunks={chunks}, done={done}")
    if text:
        print(f"  INFO  Text: {text[:100]}")
except Exception as e:
    print(f"  FAIL  {e}")

# ── 8. CORS check ─────────────────────────────────────────────────────
print("\n[8] CORS headers (browser cross-origin)")
try:
    req = urllib.request.Request(
        f"{BASE_URL}/api/documents?limit=1",
        headers={"Origin": "http://localhost:5173"}
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        cors = r.headers.get("Access-Control-Allow-Origin", "MISSING")
    print(f"  {'OK  ' if cors != 'MISSING' else 'FAIL'}  CORS: {cors}")
    if cors == "MISSING":
        print("  CAUSE Frontend will get blocked by browser — check CORS middleware")
except Exception as e:
    print(f"  FAIL  {e}")

# ── Summary ───────────────────────────────────────────────────────────
print(f"\n{LINE}")
print("  Paste the full output above and share it.")
print(LINE)