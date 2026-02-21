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
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import psycopg2
from psycopg2.extras import RealDictCursor
import faiss
import numpy as np
# Add this near the top with other imports
import pickle
import sqlite3
from pathlib import Path
import faiss
import numpy as np
from langchain_openai import OpenAIEmbeddings

# Add these global variables after your other global variables
_vector_index = None
_vector_metadata = None
_knowledge_base_conn = None

def load_vector_database():
    """Load FAISS index and metadata from your existing files."""
    global _vector_index, _vector_metadata
    
    if _vector_index is not None and _vector_metadata is not None:
        return _vector_index, _vector_metadata
    
    # Path to your existing vector database files
    index_path = Path("data/vector_databases/main_index/faiss_index.bin")
    metadata_path = Path("data/vector_databases/main_index/faiss_metadata.pkl")
    
    if not index_path.exists() or not metadata_path.exists():
        print("⚠️ Vector database files not found")
        return None, None
    
    try:
        _vector_index = faiss.read_index(str(index_path))
        with open(metadata_path, 'rb') as f:
            _vector_metadata = pickle.load(f)
        print(f"✅ Loaded FAISS index with {_vector_index.ntotal} vectors")
        return _vector_index, _vector_metadata
    except Exception as e:
        print(f"❌ Error loading vector database: {e}")
        return None, None

def get_knowledge_base():
    """Connect to your existing SQLite knowledge base."""
    global _knowledge_base_conn
    
    if _knowledge_base_conn is not None:
        return _knowledge_base_conn
    
    db_path = Path("data/knowledge_base.db")
    if not db_path.exists():
        print("⚠️ knowledge_base.db not found")
        return None
    
    try:
        _knowledge_base_conn = sqlite3.connect(str(db_path))
        _knowledge_base_conn.row_factory = sqlite3.Row
        print("✅ Connected to knowledge_base.db")
        return _knowledge_base_conn
    except Exception as e:
        print(f"❌ Error connecting to knowledge base: {e}")
        return None

def search_documents(query: str, top_k: int = 5):
    """Search for relevant documents using vector similarity."""
    index, metadata = load_vector_database()
    conn = get_knowledge_base()
    
    if not index or not metadata or not conn:
        return []
    
    try:
        # Get query embedding
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        query_embedding = embeddings.embed_query(query)
        query_vector = np.array([query_embedding]).astype('float32')
        
        # Search in FAISS
        distances, indices = index.search(query_vector, min(top_k, index.ntotal))
        
        # Get document details from SQLite
        results = []
        cursor = conn.cursor()
        
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and str(idx) in metadata:
                doc_id = metadata[str(idx)].get('id', str(idx))
                cursor.execute("""
                    SELECT id, title, author, year, type, description, tags, 
                           content_preview, source_file, page_number
                    FROM documents WHERE id = ?
                """, (doc_id,))
                row = cursor.fetchone()
                if row:
                    results.append({
                        'id': row['id'],
                        'title': row['title'],
                        'author': row['author'],
                        'year': row['year'],
                        'type': row['type'],
                        'description': row['description'],
                        'tags': row['tags'].split(',') if row['tags'] else [],
                        'content_preview': row['content_preview'],
                        'source_file': row['source_file'],
                        'page_number': row['page_number'],
                        'similarity_score': float(distances[0][i])
                    })
        
        conn.close()
        return results
        
    except Exception as e:
        print(f"❌ Error searching documents: {e}")
        return []

def get_all_documents(limit: int = 100, offset: int = 0):
    """Get all documents for the Documents page."""
    conn = get_knowledge_base()
    if not conn:
        return []
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, author, year, type, description, tags, 
               content_preview, source_file, page_number
        FROM documents
        ORDER BY year DESC
        LIMIT ? OFFSET ?
    """, (limit, offset))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'id': row['id'],
            'title': row['title'],
            'author': row['author'],
            'year': row['year'],
            'type': row['type'],
            'description': row['description'],
            'tags': row['tags'].split(',') if row['tags'] else [],
            'content_preview': row['content_preview'],
            'source_file': row['source_file'],
            'page_number': row['page_number']
        })
    
    conn.close()
    return results

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
        api_key=os.getenv("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"),
        streaming=True,
        temperature=0.7
    )


def get_embeddings():
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=os.getenv("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"),
    )


# ── Models ───────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    messages: list[dict]  # [{role: "user"|"assistant", content: str}]
    session_id: Optional[str] = None
    use_documents: bool = True  # New flag to enable/disable document search


class ChatResponse(BaseModel):
    content: str
    session_id: str
    sources: Optional[List[dict]] = None  # Add sources for citations


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
    author: str = "Unknown"
    year: int = 0
    type: str = "document"
    description: str = ""
    tags: List[str] = []
    content_preview: str = ""
    source_file: str = ""
    page_number: Optional[int] = None
    file_size: Optional[int] = None
    language: str = "en"
    similarity_score: Optional[float] = None


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


# ── Hybrid Search Functions ─────────────────────────────────────────

# Global variables to cache the vector index and metadata
_vector_index = None
_vector_metadata = None
_knowledge_base_conn = None
_embeddings = None

def get_embeddings_model():
    global _embeddings
    if _embeddings is None:
        _embeddings = get_embeddings()
    return _embeddings

def load_vector_database():
    """Load FAISS index and metadata into memory."""
    global _vector_index, _vector_metadata
    
    if _vector_index is not None and _vector_metadata is not None:
        return _vector_index, _vector_metadata
    
    index_path = Path("data/vector_databases/main_index/faiss_index.bin")
    metadata_path = Path("data/vector_databases/main_index/faiss_metadata.pkl")
    
    if not index_path.exists() or not metadata_path.exists():
        print("⚠️ Vector database not found")
        return None, None
    
    try:
        _vector_index = faiss.read_index(str(index_path))
        with open(metadata_path, 'rb') as f:
            _vector_metadata = pickle.load(f)
        print(f"✓ Loaded FAISS index with {_vector_index.ntotal} vectors")
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
        print("⚠️ Knowledge base not found")
        return None
    
    try:
        _knowledge_base_conn = sqlite3.connect(str(db_path))
        _knowledge_base_conn.row_factory = sqlite3.Row
        print("✓ Connected to knowledge base")
        return _knowledge_base_conn
    except Exception as e:
        print(f"Error connecting to knowledge base: {e}")
        return None

def search_documents_semantic(query: str, top_k: int = 5) -> List[Document]:
    """Search documents using semantic similarity with FAISS."""
    index, metadata = load_vector_database()
    conn = get_knowledge_base()
    
    if not index or not metadata or not conn:
        return []
    
    try:
        # Get query embedding
        embeddings = get_embeddings_model()
        query_embedding = embeddings.embed_query(query)
        query_vector = np.array([query_embedding]).astype('float32')
        
        # Search in FAISS
        distances, indices = index.search(query_vector, min(top_k, index.ntotal))
        
        # Get metadata for results
        results = []
        cursor = conn.cursor()
        
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and str(idx) in metadata:
                doc_id = metadata[str(idx)].get('id', str(idx))
                cursor.execute("""
                    SELECT id, title, author, year, type, description, tags, 
                           content_preview, source_file, page_number, file_size, language
                    FROM documents WHERE id = ?
                """, (doc_id,))
                row = cursor.fetchone()
                if row:
                    doc = Document(
                        id=row['id'],
                        title=row['title'],
                        author=row['author'] or "Unknown",
                        year=row['year'] or 0,
                        type=row['type'] or "document",
                        description=row['description'] or "",
                        tags=row['tags'].split(',') if row['tags'] else [],
                        content_preview=row['content_preview'] or "",
                        source_file=row['source_file'] or "",
                        page_number=row['page_number'],
                        file_size=row['file_size'],
                        language=row['language'] or "en",
                        similarity_score=float(distances[0][i])
                    )
                    results.append(doc)
        
        conn.close()
        return results
        
    except Exception as e:
        print(f"Error in semantic search: {e}")
        return []

def get_relevant_context(query: str, top_k: int = 3) -> tuple[str, List[Document]]:
    """Get relevant document context for RAG."""
    docs = search_documents_semantic(query, top_k)
    
    if not docs:
        return "", []
    
    context = "Relevant documents from the knowledge base:\n\n"
    for i, doc in enumerate(docs, 1):
        context += f"[Document {i}] {doc.title}"
        if doc.year and doc.year > 0:
            context += f" ({doc.year})"
        if doc.author and doc.author != "Unknown":
            context += f" by {doc.author}"
        context += f"\n"
        context += f"Type: {doc.type}\n"
        if doc.content_preview:
            context += f"Content: {doc.content_preview}\n"
        if doc.tags:
            context += f"Tags: {', '.join(doc.tags)}\n"
        context += "\n"
    
    return context, docs


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
    """Chat with AI using documents for context."""
    llm = get_llm()
    
    # Get the last user message
    last_user_msg = next((msg["content"] for msg in reversed(req.messages) if msg["role"] == "user"), "")
    
    # Search for relevant documents
    relevant_docs = []
    if last_user_msg:
        relevant_docs = search_documents(last_user_msg, top_k=3)
    
    # Build context from documents
    context = ""
    if relevant_docs:
        context = "Here are some relevant documents from our knowledge base:\n\n"
        for i, doc in enumerate(relevant_docs, 1):
            context += f"[Document {i}] {doc['title']}"
            if doc['author'] != "Unknown":
                context += f" by {doc['author']}"
            if doc['year']:
                context += f" ({doc['year']})"
            context += f"\n{doc['content_preview']}\n\n"
    
    # Enhance system prompt with document context
    enhanced_prompt = SYSTEM_PROMPT + "\n\n"
    if context:
        enhanced_prompt += context + "\n"
    enhanced_prompt += "Use the provided documents when relevant to give accurate, well-cited answers."

    langchain_messages = [SystemMessage(content=enhanced_prompt)]
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
    """Chat with the 1421 historian AI using hybrid search (documents + web)."""
    llm = get_llm()
    
    # Get the last user message
    last_user_msg = next((msg["content"] for msg in reversed(req.messages) if msg["role"] == "user"), "")
    
    # Get document context if enabled
    context = ""
    sources = []
    if req.use_documents and last_user_msg:
        context, sources = get_relevant_context(last_user_msg, top_k=5)
    
    # Build enhanced system prompt with document context
    enhanced_prompt = SYSTEM_PROMPT + "\n\n"
    if context:
        enhanced_prompt += context
    else:
        enhanced_prompt += "(No specific documents found - using general knowledge only)\n\n"
    
    enhanced_prompt += """When answering, follow these guidelines:
1. If you used specific documents, cite them by [Document X] references
2. Combine information from multiple sources when relevant
3. If the documents don't contain relevant information, rely on your training data
4. Be clear about what comes from documents vs general knowledge"""
    
    langchain_messages = [SystemMessage(content=enhanced_prompt)]
    for msg in req.messages:
        if msg["role"] == "user":
            langchain_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            langchain_messages.append(AIMessage(content=msg["content"]))

    try:
        response = llm.invoke(langchain_messages)
        
        # Convert sources to dict for JSON response
        sources_dict = []
        for doc in sources:
            sources_dict.append({
                "title": doc.title,
                "author": doc.author,
                "year": doc.year,
                "type": doc.type,
                "similarity": doc.similarity_score
            })
        
        return ChatResponse(
            content=response.content,
            session_id=req.session_id or datetime.now().isoformat(),
            sources=sources_dict if sources_dict else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    """Stream chat responses using LangChain with hybrid search."""
    llm = get_llm()
    
    # Get the last user message
    last_user_msg = next((msg["content"] for msg in reversed(req.messages) if msg["role"] == "user"), "")
    
    # Get document context if enabled
    context = ""
    if req.use_documents and last_user_msg:
        context, _ = get_relevant_context(last_user_msg, top_k=3)
    
    # Build enhanced system prompt
    enhanced_prompt = SYSTEM_PROMPT + "\n\n"
    if context:
        enhanced_prompt += context
    else:
        enhanced_prompt += "(No specific documents found - using general knowledge only)\n\n"

    langchain_messages = [SystemMessage(content=enhanced_prompt)]
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
    except Exception as e:
        print(f"Feedback DB error: {e}")
        pass  # DB optional — still return success
    return {"status": "ok", "message": "Feedback received"}


@app.get("/api/stats")
def get_stats():
    """Return basic system stats."""
    try:
        # Get feedback count from PostgreSQL
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
    except Exception as e:
        print(f"Stats error: {e}")
        return {
            "feedback_count": 0, 
            "locations_count": len(VOYAGE_LOCATIONS),
            "documents_count": 0
        }


# ── Document Routes ──────────────────────────────────────────────────
# Add these new endpoints after your existing ones

@app.get("/api/documents")
async def get_documents(limit: int = 50, offset: int = 0):
    """Get all documents for the Documents page."""
    documents = get_all_documents(limit, offset)
    return {
        "documents": documents,
        "total": len(documents),
        "limit": limit,
        "offset": offset
    }

@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get a specific document by ID."""
    conn = get_knowledge_base()
    if not conn:
        raise HTTPException(status_code=503, detail="Database not available")
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, author, year, type, description, tags, 
               content_preview, source_file, page_number
        FROM documents WHERE id = ?
    """, (doc_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        'id': row['id'],
        'title': row['title'],
        'author': row['author'],
        'year': row['year'],
        'type': row['type'],
        'description': row['description'],
        'tags': row['tags'].split(',') if row['tags'] else [],
        'content_preview': row['content_preview'],
        'source_file': row['source_file'],
        'page_number': row['page_number']
    }

@app.get("/api/documents/search")
async def search_documents_endpoint(q: str, limit: int = 10):
    """Search documents by query."""
    results = search_documents(q, limit)
    return {
        "results": results,
        "query": q,
        "count": len(results)
    }

@app.post("/api/documents/search", response_model=DocumentSearchResponse)
async def search_documents_endpoint(request: DocumentSearchRequest):
    """Search documents using semantic search or metadata filters."""
    start_time = time.time()
    
    try:
        if request.semantic_search and request.query:
            # Semantic search using FAISS
            documents = search_documents_semantic(request.query, request.top_k)
        else:
            # Metadata filtering (fallback)
            documents = []
            conn = get_knowledge_base()
            if conn:
                cursor = conn.cursor()
                query = "SELECT id, title, author, year, type, description, tags, content_preview, source_file, page_number, file_size, language FROM documents WHERE 1=1"
                params = []
                
                if request.filter_type:
                    query += " AND type = ?"
                    params.append(request.filter_type)
                if request.filter_year:
                    query += " AND year = ?"
                    params.append(request.filter_year)
                if request.filter_author:
                    query += " AND author LIKE ?"
                    params.append(f'%{request.filter_author}%')
                
                query += " ORDER BY year DESC LIMIT ?"
                params.append(request.top_k)
                
                cursor.execute(query, params)
                
                for row in cursor.fetchall():
                    documents.append(Document(
                        id=row['id'],
                        title=row['title'],
                        author=row['author'] or "Unknown",
                        year=row['year'] or 0,
                        type=row['type'] or "document",
                        description=row['description'] or "",
                        tags=row['tags'].split(',') if row['tags'] else [],
                        content_preview=row['content_preview'] or "",
                        source_file=row['source_file'] or "",
                        page_number=row['page_number'],
                        file_size=row['file_size'],
                        language=row['language'] or "en"
                    ))
                conn.close()
        
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
               content_preview, source_file, page_number, file_size, language
        FROM documents 
        WHERE id = ?
    """, (document_id,))
    
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")
    
    document = Document(
        id=row['id'],
        title=row['title'],
        author=row['author'] or "Unknown",
        year=row['year'] or 0,
        type=row['type'] or "document",
        description=row['description'] or "",
        tags=row['tags'].split(',') if row['tags'] else [],
        content_preview=row['content_preview'] or "",
        source_file=row['source_file'] or "",
        page_number=row['page_number'],
        file_size=row['file_size'],
        language=row['language'] or "en"
    )
    
    # Find related documents (same author)
    cursor.execute("""
        SELECT id, title, author, year, type
        FROM documents 
        WHERE author = ? AND id != ?
        ORDER BY year DESC
        LIMIT 5
    """, (row['author'], document_id))
    
    related = []
    for r in cursor.fetchall():
        related.append(Document(
            id=r['id'],
            title=r['title'],
            author=r['author'] or "Unknown",
            year=r['year'] or 0,
            type=r['type'] or "document",
            description="",
            tags=[],
            content_preview="",
            source_file=""
        ))
    
    conn.close()
    
    return DocumentDetailResponse(
        document=document,
        related_documents=related
    )


@app.get("/api/documents/types")
async def get_document_types():
    """Get all available document types for filtering."""
    conn = get_knowledge_base()
    if not conn:
        return {"types": []}
    
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT type FROM documents WHERE type IS NOT NULL ORDER BY type")
    types = [row['type'] for row in cursor.fetchall()]
    conn.close()
    return {"types": types}


@app.get("/api/documents/years")
async def get_document_years():
    """Get all available years for filtering."""
    conn = get_knowledge_base()
    if not conn:
        return {"years": []}
    
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT year FROM documents WHERE year > 0 ORDER BY year DESC")
    years = [row['year'] for row in cursor.fetchall()]
    conn.close()
    return {"years": years}


@app.get("/api/documents/authors")
async def get_document_authors():
    """Get all authors for filtering."""
    conn = get_knowledge_base()
    if not conn:
        return {"authors": []}
    
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT author FROM documents WHERE author IS NOT NULL AND author != 'Unknown' ORDER BY author")
    authors = [row['author'] for row in cursor.fetchall()]
    conn.close()
    return {"authors": authors}


# ── DB Init ──────────────────────────────────────────────────────────
@app.on_event("startup")
def init_db():
    """Create tables if they don't exist."""
    # Initialize PostgreSQL
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
        print("✓ PostgreSQL tables initialized")
    except Exception as e:
        print(f"PostgreSQL init skipped: {e}")
    
    # Initialize vector database and knowledge base
    load_vector_database()
    get_knowledge_base()