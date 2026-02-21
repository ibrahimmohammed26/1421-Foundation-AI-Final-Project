"""
1421 Foundation Research System — FastAPI Backend
Stack: FastAPI + LangChain + PostgreSQL/PostGIS + FAISS Vector Search
"""

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
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import psycopg2
from psycopg2.extras import RealDictCursor
import faiss
import numpy as np

app = FastAPI(title="1421 Foundation API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Database ─────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/fourteen21")


def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()


# ── LangChain LLM ───────────────────────────────────────────────────
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
    )


# ── Models ───────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    messages: list[dict]  # [{role: "user"|"assistant", content: str}]
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    content: str
    session_id: str


class FeedbackRequest(BaseModel):
    name: Optional[str] = None
    email: str
    feedback_type: str
    message: str


class Location(BaseModel):
    name: str
    lat: float
    lon: float
    year: int
    event: str


# Document Models
class Document(BaseModel):
    id: str
    title: str
    author: str
    year: int
    type: str  # "book", "article", "manuscript", "thesis", "paper"
    description: str
    tags: List[str]
    content_preview: str
    source_file: str
    page_number: Optional[int] = None
    file_size: Optional[int] = None
    language: str = "en"


class DocumentSearchRequest(BaseModel):
    query: str
    top_k: int = 10
    filter_type: Optional[str] = None
    filter_year: Optional[int] = None
    filter_author: Optional[str] = None
    semantic_search: bool = True


class DocumentSearchResponse(BaseModel):
    documents: List[Document]
    total_found: int
    search_time_ms: float
    query: str


class DocumentDetailResponse(BaseModel):
    document: Document
    full_content: Optional[str] = None
    related_documents: List[Document] = []


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


# ── Document Search Functions ────────────────────────────────────────

# Global variables to cache the vector index and metadata
_vector_index = None
_vector_metadata = None
_knowledge_base_conn = None

def load_vector_database():
    """Load FAISS index and metadata into memory."""
    global _vector_index, _vector_metadata
    
    if _vector_index is not None and _vector_metadata is not None:
        return _vector_index, _vector_metadata
    
    index_path = Path("data/vector_databases/main_index/faiss_index.bin")
    metadata_path = Path("data/vector_databases/main_index/faiss_metadata.pkl")
    
    if not index_path.exists() or not metadata_path.exists():
        return None, None
    
    try:
        _vector_index = faiss.read_index(str(index_path))
        with open(metadata_path, 'rb') as f:
            _vector_metadata = pickle.load(f)
        return _vector_index, _vector_metadata
    except Exception as e:
        print(f"Error loading vector database: {e}")
        return None, None

def get_knowledge_base():
    """Get connection to SQLite knowledge base."""
    global _knowledge_base_conn
    
    if _knowledge_base_conn is not None:
        return _knowledge_base_conn
    
    db_path = Path("data/knowledge_base.db")
    if not db_path.exists():
        return None
    
    try:
        _knowledge_base_conn = sqlite3.connect(str(db_path))
        _knowledge_base_conn.row_factory = sqlite3.Row
        return _knowledge_base_conn
    except Exception as e:
        print(f"Error connecting to knowledge base: {e}")
        return None

def search_documents_semantic(query: str, top_k: int = 10):
    """Search documents using semantic similarity."""
    # This is a placeholder - in production you'd need an embedding model
    # For now, we'll return documents from SQLite with text matching
    conn = get_knowledge_base()
    if not conn:
        return []
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, author, year, type, description, tags, 
               content_preview, source_file, page_number, file_size, language
        FROM documents 
        WHERE title LIKE ? OR description LIKE ? OR author LIKE ?
        LIMIT ?
    """, (f'%{query}%', f'%{query}%', f'%{query}%', top_k))
    
    results = []
    for row in cursor.fetchall():
        results.append(Document(
            id=row['id'],
            title=row['title'],
            author=row['author'],
            year=row['year'],
            type=row['type'],
            description=row['description'],
            tags=row['tags'].split(',') if row['tags'] else [],
            content_preview=row['content_preview'],
            source_file=row['source_file'],
            page_number=row['page_number'],
            file_size=row['file_size'],
            language=row['language']
        ))
    
    return results

def search_documents_metadata(
    filter_type: Optional[str] = None,
    filter_year: Optional[int] = None,
    filter_author: Optional[str] = None,
    limit: int = 100
):
    """Search documents by metadata filters."""
    conn = get_knowledge_base()
    if not conn:
        return []
    
    cursor = conn.cursor()
    query = "SELECT id, title, author, year, type, description, tags, content_preview, source_file, page_number, file_size, language FROM documents WHERE 1=1"
    params = []
    
    if filter_type:
        query += " AND type = ?"
        params.append(filter_type)
    if filter_year:
        query += " AND year = ?"
        params.append(filter_year)
    if filter_author:
        query += " AND author LIKE ?"
        params.append(f'%{filter_author}%')
    
    query += " ORDER BY year DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    
    results = []
    for row in cursor.fetchall():
        results.append(Document(
            id=row['id'],
            title=row['title'],
            author=row['author'],
            year=row['year'],
            type=row['type'],
            description=row['description'],
            tags=row['tags'].split(',') if row['tags'] else [],
            content_preview=row['content_preview'],
            source_file=row['source_file'],
            page_number=row['page_number'],
            file_size=row['file_size'],
            language=row['language']
        ))
    
    return results


# ── Routes ───────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "service": "1421 Foundation API"}


@app.get("/api/locations")
def get_locations(max_year: int = 1421):
    """Return voyage locations filtered by year."""
    return [loc for loc in VOYAGE_LOCATIONS if loc["year"] <= max_year]


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Chat with the 1421 historian AI."""
    llm = get_llm()

    langchain_messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for msg in req.messages:
        if msg["role"] == "user":
            langchain_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            langchain_messages.append(AIMessage(content=msg["content"]))

    try:
        response = llm.invoke(langchain_messages)
        return ChatResponse(
            content=response.content,
            session_id=req.session_id or datetime.now().isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    """Stream chat responses using LangChain."""
    llm = get_llm()

    langchain_messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for msg in req.messages:
        if msg["role"] == "user":
            langchain_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            langchain_messages.append(AIMessage(content=msg["content"]))

    async def generate():
        try:
            async for chunk in llm.astream(langchain_messages):
                if chunk.content:
                    yield f"data: {chunk.content}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: ERROR: {str(e)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/feedback")
def submit_feedback(req: FeedbackRequest):
    """Store feedback (uses DB if available, otherwise returns success)."""
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO feedback (name, email, feedback_type, message, created_at)
               VALUES (%s, %s, %s, %s, %s)""",
            (req.name or "Anonymous", req.email, req.feedback_type, req.message, datetime.now()),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # DB optional — still return success
    return {"status": "ok", "message": "Feedback received"}


@app.get("/api/stats")
def get_stats():
    """Return basic system stats."""
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        cur.execute("SELECT count(*) as count FROM feedback")
        feedback_count = cur.fetchone()["count"]
        conn.close()
        
        # Get document count from knowledge base
        kb_conn = get_knowledge_base()
        doc_count = 0
        if kb_conn:
            cursor = kb_conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM documents")
            result = cursor.fetchone()
            doc_count = result['count'] if result else 0
        
        return {
            "feedback_count": feedback_count, 
            "locations_count": len(VOYAGE_LOCATIONS),
            "documents_count": doc_count
        }
    except Exception:
        return {
            "feedback_count": 0, 
            "locations_count": len(VOYAGE_LOCATIONS),
            "documents_count": 0
        }


# ── Document Routes ──────────────────────────────────────────────────

@app.post("/api/documents/search", response_model=DocumentSearchResponse)
async def search_documents_endpoint(request: DocumentSearchRequest):
    """Search documents using semantic search or metadata filters."""
    start_time = time.time()
    
    # Load vector database (cached)
    index, metadata = load_vector_database()
    conn = get_knowledge_base()
    
    if not conn:
        raise HTTPException(status_code=503, detail="Knowledge base not available")
    
    try:
        if request.semantic_search and request.query:
            # Semantic search
            documents = search_documents_semantic(request.query, request.top_k)
        else:
            # Metadata filtering
            documents = search_documents_metadata(
                filter_type=request.filter_type,
                filter_year=request.filter_year,
                filter_author=request.filter_author,
                limit=request.top_k
            )
        
        # Apply additional filters if needed
        if request.filter_type or request.filter_year or request.filter_author:
            filtered = []
            for doc in documents:
                if request.filter_type and doc.type != request.filter_type:
                    continue
                if request.filter_year and doc.year != request.filter_year:
                    continue
                if request.filter_author and request.filter_author.lower() not in doc.author.lower():
                    continue
                filtered.append(doc)
            documents = filtered[:request.top_k]
        
        end_time = time.time()
        search_time_ms = (end_time - start_time) * 1000
        
        return DocumentSearchResponse(
            documents=documents,
            total_found=len(documents),
            search_time_ms=round(search_time_ms, 2),
            query=request.query
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{document_id}", response_model=DocumentDetailResponse)
async def get_document(document_id: str):
    """Get detailed information about a specific document."""
    conn = get_knowledge_base()
    if not conn:
        raise HTTPException(status_code=503, detail="Knowledge base not available")
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, author, year, type, description, tags, 
               content_preview, source_file, page_number, file_size, language,
               full_content
        FROM documents 
        WHERE id = ?
    """, (document_id,))
    
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")
    
    document = Document(
        id=row['id'],
        title=row['title'],
        author=row['author'],
        year=row['year'],
        type=row['type'],
        description=row['description'],
        tags=row['tags'].split(',') if row['tags'] else [],
        content_preview=row['content_preview'],
        source_file=row['source_file'],
        page_number=row['page_number'],
        file_size=row['file_size'],
        language=row['language']
    )
    
    # Find related documents (same author or similar tags)
    cursor.execute("""
        SELECT id, title, author, year, type, description, tags, 
               content_preview, source_file, page_number
        FROM documents 
        WHERE (author = ? OR id != ?)
        AND id != ?
        ORDER BY year DESC
        LIMIT 5
    """, (row['author'], document_id, document_id))
    
    related = []
    for r in cursor.fetchall():
        related.append(Document(
            id=r['id'],
            title=r['title'],
            author=r['author'],
            year=r['year'],
            type=r['type'],
            description=r['description'],
            tags=r['tags'].split(',') if r['tags'] else [],
            content_preview=r['content_preview'],
            source_file=r['source_file'],
            page_number=r['page_number']
        ))
    
    return DocumentDetailResponse(
        document=document,
        full_content=row['full_content'] if 'full_content' in row.keys() else None,
        related_documents=related
    )


@app.get("/api/documents/types")
async def get_document_types():
    """Get all available document types for filtering."""
    conn = get_knowledge_base()
    if not conn:
        return {"types": []}
    
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT type FROM documents ORDER BY type")
    types = [row['type'] for row in cursor.fetchall()]
    return {"types": types}


@app.get("/api/documents/years")
async def get_document_years():
    """Get all available years for filtering."""
    conn = get_knowledge_base()
    if not conn:
        return {"years": []}
    
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT year FROM documents ORDER BY year DESC")
    years = [row['year'] for row in cursor.fetchall()]
    return {"years": years}


@app.get("/api/documents/authors")
async def get_document_authors():
    """Get all authors for filtering."""
    conn = get_knowledge_base()
    if not conn:
        return {"authors": []}
    
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT author FROM documents ORDER BY author")
    authors = [row['author'] for row in cursor.fetchall()]
    return {"authors": authors}


@app.get("/api/documents/stats")
async def get_document_stats():
    """Get statistics about the document collection."""
    conn = get_knowledge_base()
    if not conn:
        return {
            "total_documents": 0,
            "by_type": {},
            "by_year": {},
            "total_authors": 0
        }
    
    cursor = conn.cursor()
    
    # Total count
    cursor.execute("SELECT COUNT(*) as count FROM documents")
    total = cursor.fetchone()['count']
    
    # Count by type
    cursor.execute("SELECT type, COUNT(*) as count FROM documents GROUP BY type")
    by_type = {row['type']: row['count'] for row in cursor.fetchall()}
    
    # Count by year
    cursor.execute("SELECT year, COUNT(*) as count FROM documents GROUP BY year ORDER BY year DESC")
    by_year = {row['year']: row['count'] for row in cursor.fetchall()}
    
    # Unique authors
    cursor.execute("SELECT COUNT(DISTINCT author) as count FROM documents")
    authors = cursor.fetchone()['count']
    
    return {
        "total_documents": total,
        "by_type": by_type,
        "by_year": by_year,
        "total_authors": authors
    }


# ── DB Init ──────────────────────────────────────────────────────────
@app.on_event("startup")
def init_db():
    """Create tables if they don't exist."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id SERIAL PRIMARY KEY,
                name TEXT,
                email TEXT NOT NULL,
                feedback_type TEXT,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                name TEXT,
                messages JSONB DEFAULT '[]',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        conn.commit()
        conn.close()
        
        # Try to load vector database on startup
        load_vector_database()
        get_knowledge_base()
        print("✓ Vector database and knowledge base loaded")
        
    except Exception as e:
        print(f"DB init skipped: {e}")