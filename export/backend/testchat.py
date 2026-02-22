"""
test_chat.py — Run from your backend folder:
    python test_chat.py

Tests the chat stream endpoint directly, bypassing the frontend entirely.
"""
import urllib.request
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"

def divider(title):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print('─'*60)

# ── 1. Check server is up ─────────────────────────────────────────────

divider("1. SERVER HEALTH")
try:
    res = urllib.request.urlopen(f"{BASE_URL}/", timeout=5)
    data = json.loads(res.read())
    print(f"  ✅ Server running: {data}")
except Exception as e:
    print(f"  ❌ Server not reachable: {e}")
    print("     Start it with: venv\\Scripts\\python.exe -m uvicorn main:app --reload")
    exit(1)

# ── 2. Check RAG context ──────────────────────────────────────────────

divider("2. RAG CONTEXT (do documents load?)")
try:
    url = f"{BASE_URL}/api/debug/rag?q=Zheng+He+voyages"
    res = urllib.request.urlopen(url, timeout=10)
    data = json.loads(res.read())
    print(f"  docs_found:    {data['docs_found']}")
    print(f"  faiss_loaded:  {data['faiss_loaded']}")
    print(f"  store_size:    {data['store_size']}")
    if data['docs_found'] == 0:
        print("  ⚠️  No docs found — RAG won't work, chat will use general knowledge only")
    else:
        print(f"  ✅ First doc: {data['doc_titles'][0][:80]}")
        print(f"  Context preview: {data['context_preview'][:200]}...")
except Exception as e:
    print(f"  ❌ RAG check failed: {e}")

# ── 3. Test non-streaming chat ────────────────────────────────────────

divider("3. NON-STREAMING CHAT (/api/chat)")
try:
    payload = json.dumps({
        "messages": [{"role": "user", "content": "In one sentence, who was Zheng He?"}],
        "use_documents": True
    }).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    res = urllib.request.urlopen(req, timeout=30)
    data = json.loads(res.read())
    print(f"  ✅ Response received!")
    print(f"  Content: {data['content'][:200]}")
    print(f"  Sources: {data.get('sources', 'none')}")
except Exception as e:
    print(f"  ❌ Non-streaming chat failed: {e}")
    print("     This means the LLM call itself is broken (check OPENAI_API_KEY)")

# ── 4. Test streaming chat ────────────────────────────────────────────

divider("4. STREAMING CHAT (/api/chat/stream)")
try:
    payload = json.dumps({
        "messages": [{"role": "user", "content": "In one sentence, who was Zheng He?"}],
        "use_documents": True
    }).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/api/chat/stream",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    res = urllib.request.urlopen(req, timeout=30)

    print("  Reading SSE stream...")
    chunks_received = 0
    full_text = ""
    error_seen = None
    done_seen = False

    raw = b""
    while True:
        chunk = res.read(256)
        if not chunk:
            break
        raw += chunk
        # Parse SSE lines
        for line in raw.split(b"\n"):
            line = line.strip()
            if not line.startswith(b"data: "):
                continue
            data = line[6:].decode("utf-8", errors="replace")
            if data == "[DONE]":
                done_seen = True
                break
            if data.startswith("ERROR:"):
                error_seen = data
                break
            # Unescape server's \n encoding
            text = data.replace("\\n", "\n")
            full_text += text
            chunks_received += 1
        raw = b""  # clear processed
        if done_seen or error_seen:
            break

    if error_seen:
        print(f"  ❌ Stream returned error: {error_seen}")
    elif done_seen:
        print(f"  ✅ Stream completed!")
        print(f"  Chunks received: {chunks_received}")
        print(f"  Full response: {full_text[:300]}")
    else:
        print(f"  ⚠️  Stream ended without [DONE] signal")
        print(f"  Chunks received: {chunks_received}")
        print(f"  Text so far: {full_text[:200]}")

except Exception as e:
    print(f"  ❌ Streaming chat failed: {e}")
    import traceback
    traceback.print_exc()

# ── 5. Check OPENAI_API_KEY ───────────────────────────────────────────

divider("5. ENVIRONMENT CHECK")
import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv("OPENAI_API_KEY", "")
if not key:
    print("  ❌ OPENAI_API_KEY is not set!")
    print("     Add it to your .env file in the backend folder:")
    print("     OPENAI_API_KEY=sk-...")
elif not key.startswith("sk-"):
    print(f"  ⚠️  OPENAI_API_KEY looks unusual: {key[:8]}...")
else:
    print(f"  ✅ OPENAI_API_KEY set: {key[:8]}...{key[-4:]}")

divider("SUMMARY")
print("  If test 3 (non-streaming) passes but test 4 (streaming) fails →")
print("    the SSE parsing in api.ts is the issue")
print()
print("  If test 3 fails with auth error →")
print("    OPENAI_API_KEY is wrong or not loaded")
print()
print("  If test 3 fails with connection error →")
print("    The LLM call itself is crashing — check main.py logs")