"""
1421 Foundation Research System - FastAPI Backend
Data source: FAISS metadata pickle (SQLite is corrupted, pickle has everything)
"""

import os
import pickle
import sqlite3
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import faiss
import numpy as np

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="1421 Foundation API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR  = Path(__file__).resolve().parents[2]
DATA_DIR  = BASE_DIR / "data"
DB_PATH   = DATA_DIR / "knowledge_base.db"
FAISS_DIR = DATA_DIR / "vector_databases" / "main_index"

# ── LLM ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a professional historian specialising in Chinese maritime exploration 
during the Ming dynasty (1368-1644), particularly the voyages of Admiral Zheng He and the 
controversial 1421 hypothesis by Gavin Menzies.

Write in clear, engaging, academic UK English. Provide comprehensive, well-structured answers 
that synthesize information. Use proper historical terminology. Be objective and balanced when 
presenting contested theories. Structure responses with clear paragraphs."""


def get_llm():
    return ChatOpenAI(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY"),
        streaming=True,
        temperature=0.7,
    )


def get_embeddings_fn():
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=os.getenv("OPENAI_API_KEY"),
    )


# ── Models ────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    messages: list[dict]
    session_id: Optional[str] = None
    use_documents: bool = True

class ChatResponse(BaseModel):
    content: str
    session_id: str
    sources: Optional[List[dict]] = None

class FeedbackRequest(BaseModel):
    name: Optional[str] = None
    email: str
    feedback_type: str
    message: str

class Document(BaseModel):
    id: str
    title: str
    author: str = "Unknown"
    year: int = 0
    type: str = "document"
    description: str = ""
    tags: List[str] = []
    content_preview: str = ""
    source_file: str = ""
    page_number: Optional[int] = None
    similarity_score: Optional[float] = None


# ── Voyage locations ──────────────────────────────────────────────────

VOYAGE_LOCATIONS = [
    {"name": "Nanjing",   "lat": 32.06, "lon": 118.80, "year": 1368, "event": "Early Ming capital established"},
    {"name": "Beijing",   "lat": 39.90, "lon": 116.41, "year": 1403, "event": "Capital moved to Beijing"},
    {"name": "Champa",    "lat": 10.82, "lon": 106.63, "year": 1405, "event": "Southeast Asian ally"},
    {"name": "Calicut",   "lat": 11.26, "lon":  75.78, "year": 1406, "event": "Zheng He fleet first arrived"},
    {"name": "Sumatra",   "lat": -0.59, "lon": 101.34, "year": 1407, "event": "Strategic trading post established"},
    {"name": "Java",      "lat": -7.61, "lon": 110.71, "year": 1407, "event": "Diplomatic missions conducted"},
    {"name": "Siam",      "lat": 13.74, "lon": 100.52, "year": 1408, "event": "Diplomatic relations established"},
    {"name": "Malacca",   "lat":  2.19, "lon": 102.25, "year": 1409, "event": "Strategic port established"},
    {"name": "Sri Lanka", "lat":  7.87, "lon":  80.77, "year": 1409, "event": "Trilingual inscription erected"},
    {"name": "Hormuz",    "lat": 27.16, "lon":  56.28, "year": 1414, "event": "Persian Gulf trade route opened"},
    {"name": "Aden",      "lat": 12.79, "lon":  45.02, "year": 1417, "event": "Arabian Peninsula contact made"},
    {"name": "Mombasa",   "lat": -4.04, "lon":  39.67, "year": 1418, "event": "East African trade commenced"},
    {"name": "Mogadishu", "lat":  2.05, "lon":  45.32, "year": 1418, "event": "Somali coast exploration"},
    {"name": "Zanzibar",  "lat": -6.17, "lon":  39.20, "year": 1419, "event": "Trade agreements established"},
]


# ── In-memory document store (loaded from pickle) ─────────────────────
# Structure of faiss_metadata.pkl:
#   {
#     "documents":    [str, ...]        # full text of each doc
#     "metadatas":    [dict, ...]       # {id, title, author, source_type, ...}
#     "document_ids": [int, ...]        # integer IDs matching metadatas index
#     "dimension":    int               # embedding dimension
#   }

_docs_store: List[dict] = []   # list of unified doc dicts, index == FAISS index
_vector_index = None
_embeddings_model = None


def _clean_text(text: str) -> str:
    """Strip leading whitespace/newlines and collapse internal whitespace runs."""
    import re
    # Remove lines that are just metadata labels (Title: / Author: / Source:)
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Skip blank lines and pure metadata header lines
        if not stripped:
            continue
        if stripped.startswith("Title:") or stripped.startswith("Author:") or stripped.startswith("Source:"):
            continue
        cleaned.append(stripped)
    result = " ".join(cleaned)
    # Collapse multiple spaces
    result = re.sub(r"  +", " ", result)
    return result.strip()


def _meta_to_doc(idx: int, text: str, meta: dict, doc_id) -> dict:
    """Convert pickle entry to our standard document dict."""
    clean  = _clean_text(text)
    title  = meta.get("title", "") or f"Document {idx+1}"
    author = meta.get("author", "Unknown") or "Unknown"
    return {
        "id":               str(doc_id),
        "title":            title,
        "author":           author,
        "year":             int(meta.get("year", 0) or 0),
        "type":             meta.get("source_type", meta.get("type", "document")) or "document",
        "description":      clean[:250] + ("..." if len(clean) > 250 else ""),
        "tags":             meta.get("tags", []) or [],
        "content_preview":  clean[:500] + ("..." if len(clean) > 500 else ""),
        "content_full":     clean,   # cleaned text used for RAG context
        "source_file":      meta.get("source", meta.get("source_type", "")) or "",
        "page_number":      meta.get("page", None),
        "similarity_score": None,
    }


def load_knowledge_base():
    """Load FAISS index + pickle into memory. Called once at startup."""
    global _docs_store, _vector_index, _embeddings_model

    meta_path  = FAISS_DIR / "faiss_metadata.pkl"
    index_path = FAISS_DIR / "faiss_index.bin"

    if not meta_path.exists():
        print(f"ERROR: {meta_path} not found")
        return

    # Load pickle
    with open(meta_path, "rb") as f:
        data = pickle.load(f)

    documents   = data.get("documents",    [])
    metadatas   = data.get("metadatas",    [])
    document_ids = data.get("document_ids", list(range(len(documents))))

    _docs_store = []
    for i in range(len(documents)):
        text = documents[i]   if i < len(documents)    else ""
        meta = metadatas[i]   if i < len(metadatas)    else {}
        did  = document_ids[i] if i < len(document_ids) else i
        _docs_store.append(_meta_to_doc(i, text, meta, did))

    print(f"OK: Loaded {len(_docs_store)} documents from pickle")

    # Load FAISS index
    if index_path.exists():
        _vector_index = faiss.read_index(str(index_path))
        print(f"OK: Loaded FAISS index with {_vector_index.ntotal} vectors")
    else:
        print(f"WARNING: FAISS index not found at {index_path}")

    # Embeddings are lazy-loaded on first search (requires OPENAI_API_KEY at query time)
    print("OK: Knowledge base ready (embeddings load on first query)")


# ── Search ────────────────────────────────────────────────────────────

def search_semantic(query: str, top_k: int = 5) -> List[dict]:
    """Vector search using FAISS — returns docs with similarity_score."""
    global _embeddings_model
    if _vector_index is None or not _docs_store:
        return []
    try:
        if _embeddings_model is None:
            _embeddings_model = get_embeddings_fn()
        vec = np.array([_embeddings_model.embed_query(query)], dtype="float32")
        distances, indices = _vector_index.search(vec, min(top_k, _vector_index.ntotal))
        results = []
        for i, idx in enumerate(indices[0]):
            if 0 <= idx < len(_docs_store):
                doc = dict(_docs_store[idx])          # copy
                doc["similarity_score"] = float(distances[0][i])
                results.append(doc)
        return results
    except Exception as e:
        print(f"ERROR semantic search: {e}")
        return []


def search_keyword(query: str, limit: int = 50) -> List[dict]:
    """Keyword search across title, author, content_preview."""
    if not _docs_store:
        return []
    q = query.lower()
    results = []
    for doc in _docs_store:
        score = 0
        if q in doc["title"].lower():           score += 3
        if q in doc["author"].lower():          score += 2
        if q in doc["content_preview"].lower(): score += 1
        if score > 0:
            d = dict(doc)
            d["similarity_score"] = score / 6.0   # normalise 0-1
            results.append(d)
    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return results[:limit]


def get_relevant_context(query: str, top_k: int = 5) -> tuple:
    """Get RAG context — semantic first, keyword fallback."""
    docs = search_semantic(query, top_k)
    if not docs:
        docs = search_keyword(query, top_k)
    if not docs:
        return "", []

    context = "Relevant documents from the 1421 Foundation knowledge base:\n\n"
    for i, doc in enumerate(docs, 1):
        context += f"[Document {i}] {doc['title']}"
        if doc.get("year") and doc["year"] > 0:
            context += f" ({doc['year']})"
        if doc.get("author") and doc["author"] != "Unknown":
            context += f" by {doc['author']}"
        context += f"\nType: {doc['type']}\n"
        # Use full content for better RAG context
        full = doc.get("content_full", doc.get("content_preview", ""))
        if full:
            context += f"Content: {full[:800]}\n"
        if doc.get("tags"):
            context += f"Tags: {', '.join(doc['tags'])}\n"
        context += "\n"

    return context, docs


# ── Routes ────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "service": "1421 Foundation API", "docs_loaded": len(_docs_store)}


@app.get("/api/locations")
def get_locations(max_year: int = 1421):
    return [loc for loc in VOYAGE_LOCATIONS if loc["year"] <= max_year]


# ── Documents ─────────────────────────────────────────────────────────

@app.get("/api/documents")
async def get_documents(limit: int = Query(default=50, le=500), offset: int = 0):
    """Return paginated documents from in-memory store."""
    if not _docs_store:
        return {"documents": [], "total": 0, "limit": limit, "offset": offset}
    total  = len(_docs_store)
    paged  = _docs_store[offset: offset + limit]
    # Strip content_full from response (not needed by frontend, saves bandwidth)
    safe   = [{k: v for k, v in d.items() if k != "content_full"} for d in paged]
    return {"documents": safe, "total": total, "limit": limit, "offset": offset}


@app.get("/api/documents/search")
async def search_documents_endpoint(q: str, limit: int = 50):
    """Search documents — semantic + keyword merged."""
    semantic = search_semantic(q, min(limit, 10))
    keyword  = search_keyword(q, limit)
    seen = {d["id"] for d in semantic}
    for d in keyword:
        if d["id"] not in seen:
            semantic.append(d)
            seen.add(d["id"])
    final = [{k: v for k, v in d.items() if k != "content_full"}
             for d in semantic[:limit]]
    return {"results": final, "total": len(final), "query": q}


@app.get("/api/documents/types")
async def get_document_types():
    types = list({d["type"] for d in _docs_store if d["type"] and d["type"] != "unknown"})
    return {"types": sorted(types)}


@app.get("/api/documents/years")
async def get_document_years():
    years = sorted({d["year"] for d in _docs_store if d["year"] and d["year"] > 0}, reverse=True)
    return {"years": years}


@app.get("/api/documents/authors")
async def get_document_authors():
    authors = sorted({d["author"] for d in _docs_store
                      if d["author"] and d["author"] != "Unknown"})
    return {"authors": authors}


# ── Chat helpers ──────────────────────────────────────────────────────

def _build_system(context: str) -> str:
    s  = SYSTEM_PROMPT + "\n\n"
    s += context if context else "(No specific documents found - using general knowledge only)\n\n"
    s += (
        "\nWhen answering:\n"
        "1. Cite relevant documents using [Document X] references\n"
        "2. Combine information from multiple sources when relevant\n"
        "3. Be clear about what comes from the documents vs general knowledge\n"
        "4. Write in academic UK English with clear paragraph structure"
    )
    return s


def _to_lc(system: str, messages: list) -> list:
    lc = [SystemMessage(content=system)]
    for m in messages:
        if m["role"] == "user":
            lc.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            lc.append(AIMessage(content=m["content"]))
    return lc


# ── Chat endpoints ────────────────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    llm  = get_llm()
    last = next((m["content"] for m in reversed(req.messages) if m["role"] == "user"), "")
    context, sources = "", []
    if req.use_documents and last:
        context, sources = get_relevant_context(last, top_k=5)
    try:
        response = llm.invoke(_to_lc(_build_system(context), req.messages))
        return ChatResponse(
            content=response.content,
            session_id=req.session_id or datetime.now().isoformat(),
            sources=[{"title": d["title"], "author": d["author"], "year": d["year"],
                      "type": d["type"], "similarity": d.get("similarity_score")}
                     for d in sources] or None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    llm  = get_llm()
    last = next((m["content"] for m in reversed(req.messages) if m["role"] == "user"), "")
    context = ""
    if req.use_documents and last:
        context, _ = get_relevant_context(last, top_k=5)

    lc_messages = _to_lc(_build_system(context), req.messages)

    async def generate():
        try:
            async for chunk in llm.astream(lc_messages):
                if chunk.content:
                    safe = chunk.content.replace("\n", "\\n")
                    yield f"data: {safe}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: ERROR: {str(e)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ── RAG debug ─────────────────────────────────────────────────────────

@app.get("/api/debug/rag")
async def debug_rag(q: str = "Zheng He voyages"):
    """
    http://localhost:8000/api/debug/rag?q=Zheng+He
    Shows exactly what gets injected into the chat prompt.
    """
    context, docs = get_relevant_context(q, top_k=5)
    return {
        "query":           q,
        "docs_found":      len(docs),
        "doc_titles":      [d["title"] for d in docs],
        "faiss_loaded":    _vector_index is not None,
        "faiss_vectors":   _vector_index.ntotal if _vector_index else 0,
        "store_size":      len(_docs_store),
        "context_preview": context[:1200] if context else "(empty - no docs matched)",
    }


# ── Feedback ──────────────────────────────────────────────────────────

@app.post("/api/feedback")
def submit_feedback(req: FeedbackRequest):
    """Store feedback - writes to a simple JSON file since SQLite is corrupted."""
    import json
    feedback_path = DATA_DIR / "feedback.json"
    try:
        existing = []
        if feedback_path.exists():
            with open(feedback_path) as f:
                existing = json.load(f)
        existing.append({
            "name":          req.name or "Anonymous",
            "email":         req.email,
            "feedback_type": req.feedback_type,
            "message":       req.message,
            "created_at":    datetime.now().isoformat(),
        })
        with open(feedback_path, "w") as f:
            json.dump(existing, f, indent=2)
    except Exception as e:
        print(f"Feedback store error: {e}")
    return {"status": "ok", "message": "Feedback received"}


# ── Stats ─────────────────────────────────────────────────────────────

@app.get("/api/stats")
def get_stats():
    import json
    feedback_count = 0
    feedback_path  = DATA_DIR / "feedback.json"
    try:
        if feedback_path.exists():
            with open(feedback_path) as f:
                feedback_count = len(json.load(f))
    except Exception:
        pass
    return {
        "feedback_count":  feedback_count,
        "locations_count": len(VOYAGE_LOCATIONS),
        "documents_count": len(_docs_store) or 347,
    }


# ── Test ──────────────────────────────────────────────────────────────

@app.get("/api/test-db")
async def test_db():
    sample = [{"id": d["id"], "title": d["title"]} for d in _docs_store[:5]]
    return {
        "store_size":    len(_docs_store),
        "faiss_loaded":  _vector_index is not None,
        "faiss_vectors": _vector_index.ntotal if _vector_index else 0,
        "sample":        sample,
    }


# ── Startup ───────────────────────────────────────────────────────────

@app.on_event("startup")
def init_app():
    print(f"BASE_DIR : {BASE_DIR}")
    print(f"DATA_DIR : {DATA_DIR}  (exists={DATA_DIR.exists()})")
    load_knowledge_base()