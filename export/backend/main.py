"""
1421 Foundation Research System — FastAPI Backend
Stack: FastAPI + LangChain + SQLite + FAISS Vector Search
"""

import json
import os
import pickle
import sqlite3
import time
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

# ── LLM ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a professional historian specialising in Chinese maritime exploration 
during the Ming dynasty (1368–1644), particularly the voyages of Admiral Zheng He and the 
controversial 1421 hypothesis by Gavin Menzies.

Write in clear, engaging, academic UK English. Provide comprehensive, well-structured answers 
that synthesize information. Use proper historical terminology. Be objective and balanced when 
presenting contested theories. Structure responses with clear paragraphs."""


def get_llm():
    return ChatOpenAI(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY"),
        streaming=True,
        temperature=0.7
    )


def get_embeddings():
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=os.getenv("OPENAI_API_KEY"),
    )


# ── Models ───────────────────────────────────────────────────────────

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


# ── Voyage Locations ─────────────────────────────────────────────────

VOYAGE_LOCATIONS = [
    {"name": "Nanjing", "lat": 32.06, "lon": 118.80, "year": 1368, "event": "Early Ming capital established"},
    {"name": "Beijing", "lat": 39.90, "lon": 116.41, "year": 1403, "event": "Capital moved to Beijing"},
    {"name": "Champa", "lat": 10.82, "lon": 106.63, "year": 1405, "event": "Southeast Asian ally"},
    {"name": "Calicut", "lat": 11.26, "lon": 75.78, "year": 1406, "event": "Zheng He fleet first arrived"},
    {"name": "Sumatra", "lat": -0.59, "lon": 101.34, "year": 1407, "event": "Strategic trading post established"},
    {"name": "Java", "lat": -7.61, "lon": 110.71, "year": 1407, "event": "Diplomatic missions conducted"},
    {"name": "Siam", "lat": 13.74, "lon": 100.52, "year": 1408, "event": "Diplomatic relations established"},
    {"name": "Malacca", "lat": 2.19, "lon": 102.25, "year": 1409, "event": "Strategic port established"},
    {"name": "Sri Lanka", "lat": 7.87, "lon": 80.77, "year": 1409, "event": "Trilingual inscription erected"},
    {"name": "Hormuz", "lat": 27.16, "lon": 56.28, "year": 1414, "event": "Persian Gulf trade route opened"},
    {"name": "Aden", "lat": 12.79, "lon": 45.02, "year": 1417, "event": "Arabian Peninsula contact made"},
    {"name": "Mombasa", "lat": -4.04, "lon": 39.67, "year": 1418, "event": "East African trade commenced"},
    {"name": "Mogadishu", "lat": 2.05, "lon": 45.32, "year": 1418, "event": "Somali coast exploration"},
    {"name": "Zanzibar", "lat": -6.17, "lon": 39.20, "year": 1419, "event": "Trade agreements established"},
]


# ── Vector DB (module-level cache) ───────────────────────────────────

_vector_index = None
_vector_metadata = None
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

    index_path = Path(__file__).resolve().parents[2] / "data" / "vector_databases" / "main_index" / "faiss_index.bin"
    metadata_path = Path(__file__).resolve().parents[2] / "data" / "vector_databases" / "main_index" / "faiss_metadata.pkl"

    if not index_path.exists() or not metadata_path.exists():
        print("⚠️  Vector database files not found")
        return None, None

    try:
        _vector_index = faiss.read_index(str(index_path))
        with open(metadata_path, "rb") as f:
            _vector_metadata = pickle.load(f)
        print(f"✅ Loaded FAISS index with {_vector_index.ntotal} vectors")
        return _vector_index, _vector_metadata
    except Exception as e:
        print(f"❌ Error loading vector database: {e}")
        return None, None


# ── SQLite helpers ────────────────────────────────────────────────────

# Data folder is at C:\Users\ibrah\1421-Foundation-AI-Final-Project\data
# This file runs from export\backend\ so we go up two levels
DB_PATH = Path(__file__).resolve().parents[2] / "data" / "knowledge_base.db"


def open_sqlite():
    """Return a fresh SQLite connection with row_factory set."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_doc(row) -> dict:
    """Convert a sqlite3.Row to a plain dict matching the Document model."""
    tags_raw = row["tags"] if "tags" in row.keys() else ""
    tags = [t.strip() for t in tags_raw.split(",")] if tags_raw else []

    content_preview = row["content_preview"] if "content_preview" in row.keys() else ""
    description = row["description"] if "description" in row.keys() else ""
    if not description and content_preview:
        description = content_preview[:200] + ("..." if len(content_preview) > 200 else "")

    return {
        "id": str(row["id"]),
        "title": row["title"] or "Untitled",
        "author": row["author"] or "Unknown",
        "year": row["year"] or 0,
        "type": row["type"] or "document",
        "description": description,
        "tags": tags,
        "content_preview": content_preview,
        "source_file": row["source_file"] if "source_file" in row.keys() else "",
        "page_number": row["page_number"] if "page_number" in row.keys() else None,
        "similarity_score": None,
    }


def get_documents_from_sqlite(limit: int = 50, offset: int = 0):
    """Return (documents, total) from SQLite — ALL columns."""
    if not DB_PATH.exists():
        return [], 0
    try:
        conn = open_sqlite()
        cursor = conn.cursor()

        # Verify table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
        if not cursor.fetchone():
            conn.close()
            return [], 0

        # Introspect available columns so we don't crash on schema differences
        cursor.execute("PRAGMA table_info(documents)")
        available = {r["name"] for r in cursor.fetchall()}

        select_cols = []
        for col in ["id", "title", "author", "year", "type", "description",
                    "tags", "content_preview", "source_file", "page_number"]:
            if col in available:
                select_cols.append(col)

        col_str = ", ".join(select_cols)

        cursor.execute(f"SELECT COUNT(*) FROM documents")
        total = cursor.fetchone()[0]

        cursor.execute(
            f"SELECT {col_str} FROM documents ORDER BY year DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        docs = [_row_to_doc(row) for row in cursor.fetchall()]
        conn.close()
        return docs, total
    except Exception as e:
        print(f"❌ SQLite get_documents error: {e}")
        return [], 0


def search_sqlite(query: str, limit: int = 50) -> List[dict]:
    """Full-text keyword search across title, author, content_preview, description."""
    if not DB_PATH.exists():
        return []
    try:
        conn = open_sqlite()
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(documents)")
        available = {r["name"] for r in cursor.fetchall()}

        select_cols = []
        for col in ["id", "title", "author", "year", "type", "description",
                    "tags", "content_preview", "source_file", "page_number"]:
            if col in available:
                select_cols.append(col)
        col_str = ", ".join(select_cols)

        q = f"%{query}%"
        search_conditions = []
        params = []
        for col in ["title", "author", "description", "content_preview", "tags"]:
            if col in available:
                search_conditions.append(f"{col} LIKE ?")
                params.append(q)

        where = " OR ".join(search_conditions) if search_conditions else "1=0"

        cursor.execute(
            f"SELECT {col_str} FROM documents WHERE {where} LIMIT ?",
            (*params, limit),
        )
        results = [_row_to_doc(row) for row in cursor.fetchall()]
        conn.close()
        return results
    except Exception as e:
        print(f"❌ SQLite search error: {e}")
        return []


# ── Semantic search (FAISS) ───────────────────────────────────────────

def search_documents_semantic(query: str, top_k: int = 5) -> List[dict]:
    """Search via FAISS then fetch full metadata from SQLite."""
    index, metadata = load_vector_database()
    if index is None or metadata is None:
        return []

    try:
        emb = get_embeddings_model()
        query_vector = np.array([emb.embed_query(query)], dtype="float32")
        distances, indices = index.search(query_vector, min(top_k, index.ntotal))

        results = []
        if DB_PATH.exists():
            conn = open_sqlite()
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(documents)")
            available = {r["name"] for r in cursor.fetchall()}
            select_cols = [c for c in ["id", "title", "author", "year", "type", "description",
                                        "tags", "content_preview", "source_file", "page_number"]
                           if c in available]
            col_str = ", ".join(select_cols)

            for i, idx in enumerate(indices[0]):
                if idx < 0:
                    continue
                meta_entry = metadata.get(str(idx), {})
                doc_id = meta_entry.get("id", str(idx))
                cursor.execute(f"SELECT {col_str} FROM documents WHERE id = ?", (doc_id,))
                row = cursor.fetchone()
                if row:
                    doc = _row_to_doc(row)
                    doc["similarity_score"] = float(distances[0][i])
                    results.append(doc)
            conn.close()
        return results
    except Exception as e:
        print(f"❌ Semantic search error: {e}")
        return []


def get_relevant_context(query: str, top_k: int = 5) -> tuple[str, List[dict]]:
    """Build RAG context string from semantic search results."""
    # Try semantic first, fall back to keyword
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


# ── Routes ───────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "service": "1421 Foundation API"}


@app.get("/api/locations")
def get_locations(max_year: int = 1421):
    return [loc for loc in VOYAGE_LOCATIONS if loc["year"] <= max_year]


# ── Documents ────────────────────────────────────────────────────────

@app.get("/api/documents")
async def get_documents(limit: int = Query(default=50, le=500), offset: int = 0):
    """
    Return paginated documents from SQLite.
    Pass limit=347 (or limit=500) to get all at once.
    """
    docs, total = get_documents_from_sqlite(limit, offset)

    # Fallback: try vector DB metadata if SQLite is empty
    if not docs:
        meta_path = Path(__file__).resolve().parents[2] / "data" / "vector_databases" / "main_index" / "faiss_metadata.pkl"
        if meta_path.exists():
            with open(meta_path, "rb") as f:
                data = pickle.load(f)
            all_docs = data.get("documents", [])
            metas = data.get("metadatas", [])
            doc_ids = data.get("document_ids", [])
            total = len(all_docs)
            for i in range(offset, min(offset + limit, total)):
                meta = metas[i] if i < len(metas) else {}
                source = meta.get("source", "")
                docs.append({
                    "id": doc_ids[i] if i < len(doc_ids) else str(i),
                    "title": Path(source).stem if source else f"Document {i+1}",
                    "author": meta.get("author", "Unknown"),
                    "year": meta.get("year", 0),
                    "type": meta.get("type", "document"),
                    "description": (all_docs[i][:200] + "...") if len(all_docs[i]) > 200 else all_docs[i],
                    "tags": meta.get("tags", []),
                    "content_preview": (all_docs[i][:500] + "...") if len(all_docs[i]) > 500 else all_docs[i],
                    "source_file": source,
                    "page_number": meta.get("page", None),
                    "similarity_score": None,
                })

    return {"documents": docs, "total": total, "limit": limit, "offset": offset}


@app.get("/api/documents/search")
async def search_documents_endpoint(q: str, limit: int = 50):
    """Search documents — tries SQLite keyword search then semantic."""
    results = search_sqlite(q, limit)
    # Boost with semantic if we have FAISS
    semantic = search_documents_semantic(q, min(limit, 10))
    # Merge: semantic results first, then keyword-only hits
    seen = {r["id"] for r in semantic}
    for r in results:
        if r["id"] not in seen:
            semantic.append(r)
            seen.add(r["id"])
    return {"results": semantic[:limit], "total": len(semantic[:limit]), "query": q}


@app.get("/api/documents/types")
async def get_document_types():
    if not DB_PATH.exists():
        return {"types": []}
    conn = open_sqlite()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT type FROM documents WHERE type IS NOT NULL AND type != '' AND type != 'unknown'")
    types = [row[0] for row in cursor.fetchall()]
    conn.close()
    return {"types": types}


@app.get("/api/documents/years")
async def get_document_years():
    if not DB_PATH.exists():
        return {"years": []}
    conn = open_sqlite()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT year FROM documents WHERE year > 0 ORDER BY year DESC")
    years = [row[0] for row in cursor.fetchall()]
    conn.close()
    return {"years": years}


@app.get("/api/documents/authors")
async def get_document_authors():
    if not DB_PATH.exists():
        return {"authors": []}
    conn = open_sqlite()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT author FROM documents WHERE author IS NOT NULL AND author != '' AND author != 'Unknown'")
    authors = [row[0] for row in cursor.fetchall()]
    conn.close()
    return {"authors": authors}


# ── Chat ─────────────────────────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    llm = get_llm()
    last_user_msg = next(
        (m["content"] for m in reversed(req.messages) if m["role"] == "user"), ""
    )

    context, sources = "", []
    if req.use_documents and last_user_msg:
        context, sources = get_relevant_context(last_user_msg, top_k=5)

    system = SYSTEM_PROMPT + "\n\n"
    system += context if context else "(No specific documents found — using general knowledge only)\n\n"
    system += (
        "\nWhen answering:\n"
        "1. Cite relevant documents using [Document X] references\n"
        "2. Combine information from multiple sources when relevant\n"
        "3. Be clear about what comes from the documents vs general knowledge\n"
        "4. Write in academic UK English with clear paragraph structure"
    )

    lc_messages = [SystemMessage(content=system)]
    for msg in req.messages:
        if msg["role"] == "user":
            lc_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            lc_messages.append(AIMessage(content=msg["content"]))

    try:
        response = llm.invoke(lc_messages)
        return ChatResponse(
            content=response.content,
            session_id=req.session_id or datetime.now().isoformat(),
            sources=[
                {"title": d["title"], "author": d["author"], "year": d["year"],
                 "type": d["type"], "similarity": d.get("similarity_score")}
                for d in sources
            ] or None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    llm = get_llm()
    last_user_msg = next(
        (m["content"] for m in reversed(req.messages) if m["role"] == "user"), ""
    )

    context = ""
    if req.use_documents and last_user_msg:
        context, _ = get_relevant_context(last_user_msg, top_k=5)

    system = SYSTEM_PROMPT + "\n\n"
    system += context if context else "(No specific documents found — using general knowledge only)\n\n"
    system += (
        "\nWhen answering:\n"
        "1. Cite relevant documents using [Document X] references\n"
        "2. Combine information from multiple sources when relevant\n"
        "3. Be clear about what comes from the documents vs general knowledge\n"
        "4. Write in academic UK English with clear paragraph structure"
    )

    lc_messages = [SystemMessage(content=system)]
    for msg in req.messages:
        if msg["role"] == "user":
            lc_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            lc_messages.append(AIMessage(content=msg["content"]))

    async def generate():
        try:
            async for chunk in llm.astream(lc_messages):
                if chunk.content:
                    # Escape newlines so SSE stays on one data: line
                    safe = chunk.content.replace("\n", "\\n")
                    yield f"data: {safe}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: ERROR: {str(e)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ── Feedback ─────────────────────────────────────────────────────────

@app.post("/api/feedback")
def submit_feedback(req: FeedbackRequest):
    # Store in SQLite feedback table if available (no PostgreSQL dependency)
    try:
        if DB_PATH.exists():
            conn = sqlite3.connect(str(DB_PATH))
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT, email TEXT NOT NULL,
                    feedback_type TEXT, message TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.execute(
                "INSERT INTO feedback (name, email, feedback_type, message) VALUES (?,?,?,?)",
                (req.name or "Anonymous", req.email, req.feedback_type, req.message),
            )
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"Feedback store error: {e}")
    return {"status": "ok", "message": "Feedback received"}


# ── Stats ─────────────────────────────────────────────────────────────

@app.get("/api/stats")
def get_stats():
    doc_count = 0
    feedback_count = 0
    try:
        if DB_PATH.exists():
            conn = sqlite3.connect(str(DB_PATH))
            row = conn.execute("SELECT COUNT(*) FROM documents").fetchone()
            doc_count = row[0] if row else 0
            try:
                row = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()
                feedback_count = row[0] if row else 0
            except Exception:
                pass
            conn.close()
    except Exception as e:
        print(f"Stats error: {e}")

    return {
        "feedback_count": feedback_count,
        "locations_count": len(VOYAGE_LOCATIONS),
        "documents_count": doc_count or 347,
    }


# ── Debug ─────────────────────────────────────────────────────────────

@app.get("/api/test-db")
async def test_db():
    sqlite_docs, sqlite_total = get_documents_from_sqlite(5, 0)
    index, _ = load_vector_database()
    return {
        "sqlite": {
            "exists": DB_PATH.exists(),
            "document_count": sqlite_total,
            "sample_titles": [d["title"] for d in sqlite_docs],
        },
        "vector_db": {
            "faiss_exists": Path(__file__).resolve().parents[2] / "data" / "vector_databases" / "main_index" / "faiss_index.bin".exists(),
            "vectors": index.ntotal if index else 0,
        },
    }


# ── Startup ───────────────────────────────────────────────────────────

@app.on_event("startup")
def init_app():
    load_vector_database()
    if DB_PATH.exists():
        print(f"✅ SQLite database found: {DB_PATH}")
    else:
        print("⚠️  SQLite database not found — run the indexer first")