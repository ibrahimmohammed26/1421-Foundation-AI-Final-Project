"""
1421 Foundation Research System - FastAPI Backend
Stack: FastAPI + LangChain + SQLite + FAISS Vector Search
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

# Paths - main.py lives at .../export/backend/main.py
#         data/ lives at   .../data/
BASE_DIR  = Path(__file__).resolve().parents[2]
DATA_DIR  = BASE_DIR / "data"
DB_PATH   = DATA_DIR / "knowledge_base.db"
FAISS_DIR = DATA_DIR / "vector_databases" / "main_index"

# LLM

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


def get_embeddings():
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=os.getenv("OPENAI_API_KEY"),
    )


# Models

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


# Voyage locations

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


# Vector DB cache

_vector_index     = None
_vector_metadata  = None
_embeddings_model = None


def get_embeddings_model():
    global _embeddings_model
    if _embeddings_model is None:
        _embeddings_model = get_embeddings()
    return _embeddings_model


def load_vector_database():
    global _vector_index, _vector_metadata
    if _vector_index is not None:
        return _vector_index, _vector_metadata

    index_path    = FAISS_DIR / "faiss_index.bin"
    metadata_path = FAISS_DIR / "faiss_metadata.pkl"

    if not index_path.exists() or not metadata_path.exists():
        print(f"WARNING: Vector database files not found in {FAISS_DIR}")
        return None, None

    try:
        _vector_index = faiss.read_index(str(index_path))
        with open(metadata_path, "rb") as f:
            _vector_metadata = pickle.load(f)
        print(f"OK: Loaded FAISS index with {_vector_index.ntotal} vectors")
        if isinstance(_vector_metadata, dict):
            print(f"   Metadata top-level keys: {list(_vector_metadata.keys())[:8]}")
        return _vector_index, _vector_metadata
    except Exception as e:
        print(f"ERROR loading vector database: {e}")
        return None, None


# SQLite helpers

def open_sqlite():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_doc(row) -> dict:
    keys            = row.keys()
    tags_raw        = row["tags"]            if "tags"            in keys else ""
    content_preview = row["content_preview"] if "content_preview" in keys else ""
    description     = row["description"]     if "description"     in keys else ""
    tags = [t.strip() for t in tags_raw.split(",")] if tags_raw else []
    if not description and content_preview:
        description = content_preview[:200] + ("..." if len(content_preview) > 200 else "")
    return {
        "id":               str(row["id"]),
        "title":            row["title"]       or "Untitled",
        "author":           row["author"]      or "Unknown",
        "year":             row["year"]        or 0,
        "type":             row["type"]        or "document",
        "description":      description,
        "tags":             tags,
        "content_preview":  content_preview,
        "source_file":      row["source_file"] if "source_file" in keys else "",
        "page_number":      row["page_number"] if "page_number" in keys else None,
        "similarity_score": None,
    }


def _get_cols() -> list:
    conn = open_sqlite()
    available = {r["name"] for r in conn.execute("PRAGMA table_info(documents)").fetchall()}
    conn.close()
    return [c for c in ["id","title","author","year","type","description",
                         "tags","content_preview","source_file","page_number"]
            if c in available]


def get_documents_from_sqlite(limit: int = 50, offset: int = 0):
    if not DB_PATH.exists():
        return [], 0
    try:
        conn   = open_sqlite()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
        if not cursor.fetchone():
            conn.close()
            return [], 0
        cols  = _get_cols()
        total = cursor.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        cursor.execute(
            f"SELECT {', '.join(cols)} FROM documents ORDER BY year DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        docs = [_row_to_doc(r) for r in cursor.fetchall()]
        conn.close()
        return docs, total
    except Exception as e:
        print(f"ERROR get_documents_from_sqlite: {e}")
        return [], 0


def search_sqlite(query: str, limit: int = 50) -> List[dict]:
    if not DB_PATH.exists():
        return []
    try:
        conn      = open_sqlite()
        cursor    = conn.cursor()
        available = {r["name"] for r in cursor.execute("PRAGMA table_info(documents)").fetchall()}
        cols      = [c for c in ["id","title","author","year","type","description",
                                  "tags","content_preview","source_file","page_number"]
                     if c in available]
        q      = f"%{query}%"
        conds  = []
        params = []
        for col in ["title","author","description","content_preview","tags"]:
            if col in available:
                conds.append(f"{col} LIKE ?")
                params.append(q)
        where = " OR ".join(conds) if conds else "1=0"
        cursor.execute(
            f"SELECT {', '.join(cols)} FROM documents WHERE {where} LIMIT ?",
            (*params, limit),
        )
        results = [_row_to_doc(r) for r in cursor.fetchall()]
        conn.close()
        return results
    except Exception as e:
        print(f"ERROR search_sqlite: {e}")
        return []


# Semantic search

def _doc_id_from_meta(metadata, faiss_idx: int) -> str:
    """
    Handles three common metadata formats:
      1. dict keyed by str(faiss_idx):  {"0": {"id": "abc"}, ...}
      2. dict with list values:         {"metadatas": [...], "document_ids": [...]}
      3. plain list:                    [{"id": "abc"}, ...]
    """
    if isinstance(metadata, dict):
        entry = metadata.get(str(faiss_idx))
        if isinstance(entry, dict):
            return str(entry.get("id", faiss_idx))
        doc_ids = metadata.get("document_ids", [])
        if doc_ids and faiss_idx < len(doc_ids):
            return str(doc_ids[faiss_idx])
        metas = metadata.get("metadatas", [])
        if metas and faiss_idx < len(metas):
            m = metas[faiss_idx]
            return str(m.get("id", faiss_idx)) if isinstance(m, dict) else str(faiss_idx)
    elif isinstance(metadata, list) and faiss_idx < len(metadata):
        m = metadata[faiss_idx]
        return str(m.get("id", faiss_idx)) if isinstance(m, dict) else str(faiss_idx)
    return str(faiss_idx)


def search_documents_semantic(query: str, top_k: int = 5) -> List[dict]:
    index, metadata = load_vector_database()
    if index is None or metadata is None:
        return []
    try:
        vec = np.array([get_embeddings_model().embed_query(query)], dtype="float32")
        distances, indices = index.search(vec, min(top_k, index.ntotal))

        if not DB_PATH.exists():
            return []

        conn      = open_sqlite()
        cursor    = conn.cursor()
        cols      = _get_cols()

        results = []
        for i, idx in enumerate(indices[0]):
            if idx < 0:
                continue
            doc_id = _doc_id_from_meta(metadata, int(idx))
            row    = cursor.execute(
                f"SELECT {', '.join(cols)} FROM documents WHERE id = ?", (doc_id,)
            ).fetchone()
            if row:
                doc = _row_to_doc(row)
                doc["similarity_score"] = float(distances[0][i])
                results.append(doc)

        conn.close()
        if not results:
            print("WARNING: FAISS returned indices but 0 SQLite matches - id format mismatch? Falling back to keyword.")
        return results
    except Exception as e:
        print(f"ERROR semantic search: {e}")
        return []


def get_relevant_context(query: str, top_k: int = 5) -> tuple:
    docs = search_documents_semantic(query, top_k)
    if not docs:
        docs = search_sqlite(query, top_k)
    if not docs:
        return "", []

    context = "Relevant documents from the 1421 Foundation knowledge base:\n\n"
    for i, doc in enumerate(docs, 1):
        context += f"[Document {i}] {doc['title']}"
        if doc.get("year") and doc["year"] > 0:
            context += f" ({doc['year']})"
        if doc.get("author") and doc["author"] != "Unknown":
            context += f" by {doc['author']}"
        context += "\n"
        if doc.get("type"):
            context += f"Type: {doc['type']}\n"
        if doc.get("content_preview"):
            context += f"Content: {doc['content_preview'][:600]}\n"
        if doc.get("tags"):
            context += f"Tags: {', '.join(doc['tags'])}\n"
        context += "\n"
    return context, docs


# Routes

@app.get("/")
def root():
    return {"status": "ok", "service": "1421 Foundation API"}


@app.get("/api/locations")
def get_locations(max_year: int = 1421):
    return [loc for loc in VOYAGE_LOCATIONS if loc["year"] <= max_year]


# Documents

@app.get("/api/documents")
async def get_documents(limit: int = Query(default=50, le=500), offset: int = 0):
    docs, total = get_documents_from_sqlite(limit, offset)

    if not docs:
        meta_path = FAISS_DIR / "faiss_metadata.pkl"
        if meta_path.exists():
            with open(meta_path, "rb") as f:
                data = pickle.load(f)
            all_docs = data.get("documents", [])
            metas    = data.get("metadatas", [])
            doc_ids  = data.get("document_ids", [])
            total    = len(all_docs)
            for i in range(offset, min(offset + limit, total)):
                meta   = metas[i]   if i < len(metas)   else {}
                source = meta.get("source", "") if isinstance(meta, dict) else ""
                text   = all_docs[i]            if i < len(all_docs)  else ""
                docs.append({
                    "id":               doc_ids[i] if i < len(doc_ids) else str(i),
                    "title":            Path(source).stem if source else f"Document {i+1}",
                    "author":           meta.get("author", "Unknown") if isinstance(meta, dict) else "Unknown",
                    "year":             meta.get("year",   0)          if isinstance(meta, dict) else 0,
                    "type":             meta.get("type",   "document") if isinstance(meta, dict) else "document",
                    "description":      (text[:200] + "...") if len(text) > 200 else text,
                    "tags":             meta.get("tags", []) if isinstance(meta, dict) else [],
                    "content_preview":  (text[:500] + "...") if len(text) > 500 else text,
                    "source_file":      source,
                    "page_number":      meta.get("page", None) if isinstance(meta, dict) else None,
                    "similarity_score": None,
                })

    return {"documents": docs, "total": total, "limit": limit, "offset": offset}


@app.get("/api/documents/search")
async def search_documents_endpoint(q: str, limit: int = 50):
    semantic = search_documents_semantic(q, min(limit, 10))
    keyword  = search_sqlite(q, limit)
    seen = {r["id"] for r in semantic}
    for r in keyword:
        if r["id"] not in seen:
            semantic.append(r)
            seen.add(r["id"])
    final = semantic[:limit]
    return {"results": final, "total": len(final), "query": q}


@app.get("/api/documents/types")
async def get_document_types():
    if not DB_PATH.exists():
        return {"types": []}
    conn  = open_sqlite()
    types = [r[0] for r in conn.execute(
        "SELECT DISTINCT type FROM documents WHERE type IS NOT NULL AND type != '' AND type != 'unknown'"
    ).fetchall()]
    conn.close()
    return {"types": types}


@app.get("/api/documents/years")
async def get_document_years():
    if not DB_PATH.exists():
        return {"years": []}
    conn  = open_sqlite()
    years = [r[0] for r in conn.execute(
        "SELECT DISTINCT year FROM documents WHERE year > 0 ORDER BY year DESC"
    ).fetchall()]
    conn.close()
    return {"years": years}


@app.get("/api/documents/authors")
async def get_document_authors():
    if not DB_PATH.exists():
        return {"authors": []}
    conn    = open_sqlite()
    authors = [r[0] for r in conn.execute(
        "SELECT DISTINCT author FROM documents WHERE author IS NOT NULL AND author != '' AND author != 'Unknown'"
    ).fetchall()]
    conn.close()
    return {"authors": authors}


# Chat helpers

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


# Chat endpoints

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


# RAG debug - open in browser to verify documents are being used

@app.get("/api/debug/rag")
async def debug_rag(q: str = "Zheng He voyages"):
    """
    Visit: http://localhost:8000/api/debug/rag?q=Zheng+He
    Shows exactly what context gets injected into the chat prompt.
    """
    context, docs = get_relevant_context(q, top_k=5)
    return {
        "query":           q,
        "docs_found":      len(docs),
        "doc_titles":      [d["title"] for d in docs],
        "faiss_loaded":    _vector_index is not None,
        "faiss_vectors":   _vector_index.ntotal if _vector_index else 0,
        "sqlite_exists":   DB_PATH.exists(),
        "context_preview": context[:1000] if context else "(empty - no docs matched)",
    }


# Feedback

@app.post("/api/feedback")
def submit_feedback(req: FeedbackRequest):
    try:
        if DB_PATH.exists():
            conn = sqlite3.connect(str(DB_PATH))
            conn.execute("""CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, email TEXT NOT NULL,
                feedback_type TEXT, message TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')))""")
            conn.execute(
                "INSERT INTO feedback (name,email,feedback_type,message) VALUES (?,?,?,?)",
                (req.name or "Anonymous", req.email, req.feedback_type, req.message),
            )
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"Feedback store error: {e}")
    return {"status": "ok", "message": "Feedback received"}


# Stats

@app.get("/api/stats")
def get_stats():
    doc_count = feedback_count = 0
    try:
        if DB_PATH.exists():
            conn = sqlite3.connect(str(DB_PATH))
            doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            try:
                feedback_count = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
            except Exception:
                pass
            conn.close()
    except Exception as e:
        print(f"Stats error: {e}")
    return {
        "feedback_count":  feedback_count,
        "locations_count": len(VOYAGE_LOCATIONS),
        "documents_count": doc_count or 347,
    }


# Test DB

@app.get("/api/test-db")
async def test_db():
    sqlite_docs, sqlite_total = get_documents_from_sqlite(5, 0)
    index, meta = load_vector_database()
    faiss_path  = FAISS_DIR / "faiss_index.bin"
    meta_keys   = list(meta.keys())[:5] if isinstance(meta, dict) else str(type(meta))
    return {
        "sqlite": {
            "exists":         DB_PATH.exists(),
            "document_count": sqlite_total,
            "sample_titles":  [d["title"] for d in sqlite_docs],
        },
        "vector_db": {
            "faiss_exists": faiss_path.exists(),
            "vectors":      index.ntotal if index else 0,
            "meta_keys":    meta_keys,
        },
    }


# Startup

@app.on_event("startup")
def init_app():
    print(f"BASE_DIR : {BASE_DIR}")
    print(f"DB_PATH  : {DB_PATH}  (exists={DB_PATH.exists()})")
    print(f"FAISS_DIR: {FAISS_DIR}  (exists={FAISS_DIR.exists()})")
    load_vector_database()