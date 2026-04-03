"""
1421 Foundation Research System - FastAPI Backend
"""

import os
import re
import pickle
import resend
import json
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from pydantic import BaseModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import faiss
import numpy as np

from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
print(f"OPENAI_API_KEY loaded: {'Yes' if api_key else 'No'}")

app = FastAPI(title="1421 Foundation API", version="1.0.0")

VERCEL_ORIGIN = "https://1421-foundation-ai-final-project.vercel.app"

class CORSEverythingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return Response(
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": VERCEL_ORIGIN,
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept",
                    "Access-Control-Max-Age": "3600",
                }
            )
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = VERCEL_ORIGIN
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept"
        return response

app.add_middleware(CORSEverythingMiddleware)

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) == "/":
    BASE_DIR = Path("/workspace/backend")
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR.parent / "data")))
FAISS_DIR = DATA_DIR / "vector_databases" / "main_index"

# ── Email ─────────────────────────────────────────────────────────────
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
NOTIFY_EMAIL   = os.getenv("NOTIFY_EMAIL", "")

def send_feedback_email(name, email, feedback_type, message):
    if not RESEND_API_KEY:
        return
    try:
        resend.api_key = RESEND_API_KEY
        to_addr = NOTIFY_EMAIL or "ibrahimalim2605@gmail.com"
        resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": to_addr,
            "subject": f"[1421 Foundation] New Feedback: {feedback_type}",
            "html": f"""
                <h2 style="color:#8B0000;">New Feedback</h2>
                <p><b>Name:</b> {name}</p><p><b>Email:</b> {email}</p>
                <p><b>Type:</b> {feedback_type}</p>
                <p><b>Message:</b> {message}</p>
            """
        })
    except Exception as e:
        print(f"Email error: {e}")

# ── System prompts ────────────────────────────────────────────────────

SYSTEM_PROMPT_WITH_DOCS = """You are a research assistant for the 1421 Foundation, specialising in Chinese maritime exploration during the Ming dynasty (1368–1644), particularly the voyages of Admiral Zheng He and the 1421 hypothesis by Gavin Menzies.

RULES:
1. Answer primarily from the documents provided. Cite every claim using [Document X] inline.
2. YOU CAN INFER AND SYNTHESIZE across documents to give a complete answer.
3. You may supplement with your general historical knowledge where the documents do not cover a point — but when you do, add the note (general knowledge) inline at that point so the reader knows.
4. Write in clear, academic UK English with clear paragraphs."""

SYSTEM_PROMPT_WEB_FALLBACK = """You are a research assistant for the 1421 Foundation, specialising in Chinese maritime exploration during the Ming dynasty (1368–1644), particularly the voyages of Admiral Zheng He and the 1421 hypothesis by Gavin Menzies.

No documents from the 1421 Foundation knowledge base matched this query. You are answering from your general training knowledge.

RULES:
1. Answer as helpfully and accurately as possible from your general knowledge.
2. Do NOT fabricate [Document X] citations — there are no documents to cite.
3. Be clear, factual, and academic. Write in clear UK English."""


def get_llm():
    return ChatOpenAI(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY"),
        streaming=True,
        temperature=0.3,
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
    used_web_fallback: bool = False

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
    url: str = ""
    page_number: Optional[int] = None
    similarity_score: Optional[float] = None

# ── Voyage locations ──────────────────────────────────────────────────

VOYAGE_LOCATIONS = [
    {"name": "Nanjing",   "lat": 32.06,  "lon": 118.80, "year": 1403, "event": "Yongle Emperor commissions the treasure fleet from Nanjing"},
    {"name": "Nanjing",   "lat": 32.06,  "lon": 118.80, "year": 1405, "event": "First voyage departs — 317 ships and 28,000 men set sail"},
    {"name": "Champa",    "lat": 10.82,  "lon": 106.63, "year": 1405, "event": "First stop on Voyage 1 — Southeast Asian ally (modern Vietnam)"},
    {"name": "Java",      "lat": -7.61,  "lon": 110.71, "year": 1406, "event": "Voyage 1 — diplomatic missions conducted on Java"},
    {"name": "Sumatra",   "lat": -0.59,  "lon": 101.34, "year": 1406, "event": "Voyage 1 — strategic trading post established at Palembang"},
    {"name": "Malacca",   "lat":  2.19,  "lon": 102.25, "year": 1406, "event": "Voyage 1 — key port established, local piracy suppressed"},
    {"name": "Calicut",   "lat": 11.26,  "lon":  75.78, "year": 1407, "event": "Voyage 1 — primary destination on the Malabar Coast, India"},
    {"name": "Siam",      "lat": 13.74,  "lon": 100.52, "year": 1408, "event": "Voyage 2 — diplomatic relations established (modern Thailand)"},
    {"name": "Sri Lanka", "lat":  7.87,  "lon":  80.77, "year": 1409, "event": "Voyage 2 — trilingual inscription erected at Galle"},
    {"name": "Hormuz",    "lat": 27.16,  "lon":  56.28, "year": 1414, "event": "Voyage 4 — Persian Gulf reached for first time, 18 states sent tribute"},
    {"name": "Aden",      "lat": 12.79,  "lon":  45.02, "year": 1417, "event": "Voyage 5 — Arabian Peninsula reached, gifts of zebras and lions received"},
    {"name": "Mogadishu", "lat":  2.05,  "lon":  45.32, "year": 1418, "event": "Voyage 5 — Somali coast, first Chinese fleet to reach East Africa"},
    {"name": "Malindi",   "lat": -3.22,  "lon":  40.12, "year": 1418, "event": "Voyage 5 — Kenya coast, famous giraffe gifted to the Yongle Emperor"},
    {"name": "Mombasa",   "lat": -4.04,  "lon":  39.67, "year": 1419, "event": "Voyage 5 — East African trade firmly established"},
    {"name": "Zanzibar",  "lat": -6.17,  "lon":  39.20, "year": 1421, "event": "Voyage 6 — southernmost point of the treasure fleet voyages"},
    {"name": "Jidda",     "lat": 21.49,  "lon":  39.19, "year": 1432, "event": "Voyage 7 — Red Sea reached, auxiliary fleet sent towards Mecca"},
    {"name": "Calicut",   "lat": 11.26,  "lon":  75.78, "year": 1433, "event": "Voyage 7 — Zheng He dies here on the return journey, ending the voyages"},
]

# ── Document store ────────────────────────────────────────────────────

_docs_store: List[dict] = []
_vector_index = None
_embeddings_model = None

def _clean_text(text: str) -> str:
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.lower().startswith("content:"):
            value = stripped[8:].strip()
            if value:
                cleaned.append(value)
            continue
        matched = False
        for prefix in ("Title:", "Author:", "Source:", "Type:", "Tags:"):
            if stripped.startswith(prefix):
                value = stripped[len(prefix):].strip()
                if prefix == "Source:" and value:
                    cleaned.append(value)
                matched = True
                break
        if not matched:
            cleaned.append(stripped)
    return re.sub(r"  +", " ", " ".join(cleaned)).strip()

def _meta_to_doc(idx: int, text: str, meta: dict, doc_id) -> dict:
    clean = _clean_text(text)
    title = (meta.get("title", "") or "").strip()
    for line in text.split("\n"):
        s = line.strip()
        if s.lower().startswith("title:"):
            candidate = s[6:].strip()
            if len(candidate) > len(title):
                title = candidate
            break
    if not title:
        first = clean.split(".")[0].strip()
        title = first[:200] if first else f"Document {idx+1}"
    return {
        "id":               str(doc_id),
        "title":            title,
        "author":           meta.get("author", "Unknown") or "Unknown",
        "year":             int(meta.get("year", 0) or 0),
        "type":             meta.get("source_type", meta.get("type", "document")) or "document",
        "description":      clean,
        "tags":             meta.get("tags", []) or [],
        "content_preview":  clean,
        "content_full":     clean,
        "source_file":      meta.get("source_file", meta.get("source", "")) or "",
        "url":              meta.get("url", "") or "",
        "page_number":      meta.get("page", None),
        "similarity_score": None,
        "_relevance_score": 0.0,  # internal ranking score
    }

def load_knowledge_base():
    global _docs_store, _vector_index, _embeddings_model
    
    meta_path = FAISS_DIR / "faiss_metadata.pkl"
    index_path = FAISS_DIR / "faiss_index.bin"
    
    if not meta_path.exists():
        print(f"ERROR: {meta_path} not found")
        print(f"Please ensure faiss_metadata.pkl is in {FAISS_DIR}")
        return
    
    try:
        with open(meta_path, "rb") as f:
            data = pickle.load(f)
        
        if isinstance(data, dict):
            documents = data.get("documents", [])
            metadatas = data.get("metadatas", [])
            print(f"✅ Dictionary format: {len(documents)} docs")
        elif isinstance(data, list):
            print("⚠️  Legacy list format, converting...")
            metadatas = data
            documents = [f"Document {i+1}" for i in range(len(metadatas))]
            print(f"✅ Converted: {len(documents)} docs")
        else:
            print(f"❌ Unexpected format: {type(data)}")
            return
        
        if len(documents) != len(metadatas):
            print(f"⚠️  Length mismatch, adjusting...")
            min_len = min(len(documents), len(metadatas))
            documents = documents[:min_len]
            metadatas = metadatas[:min_len]
        
        _docs_store = []
        for i in range(len(documents)):
            doc_text = documents[i] if i < len(documents) else ""
            doc_meta = metadatas[i] if i < len(metadatas) else {}
            _docs_store.append(_meta_to_doc(i, doc_text, doc_meta, i + 1))
        
        print(f"✅ Loaded {len(_docs_store)} documents")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    if index_path.exists():
        try:
            _vector_index = faiss.read_index(str(index_path))
            print(f"✅ FAISS index: {_vector_index.ntotal} vectors")
        except Exception as e:
            print(f"❌ FAISS error: {e}")
            _vector_index = None
    else:
        print(f"⚠️  FAISS index not found")
        _vector_index = None
    
    print("✅ Knowledge base ready")
    global _docs_store, _vector_index, _embeddings_model
    meta_path  = FAISS_DIR / "faiss_metadata.pkl"
    index_path = FAISS_DIR / "faiss_index.bin"
    
    if not meta_path.exists():
        print(f"ERROR: {meta_path} not found")
        print(f"Please ensure faiss_metadata.pkl is in {FAISS_DIR}")
        return
    
    try:
        with open(meta_path, "rb") as f:
            data = pickle.load(f)
        
        # ✅ Handle both dictionary and list formats
        if isinstance(data, dict):
            # New format: dictionary with 'documents' and 'metadatas' keys
            documents = data.get("documents", [])
            metadatas = data.get("metadatas", [])
            print(f"✅ Loaded dictionary format: {len(documents)} documents, {len(metadatas)} metadata entries")
        elif isinstance(data, list):
            # Old format: list of metadata only
            print("⚠️  Legacy list format detected. Converting to support both formats...")
            metadatas = data
            # Create placeholder documents for backward compatibility
            documents = [f"Document {i+1}" for i in range(len(metadatas))]
            print(f"✅ Converted list format: {len(documents)} documents")
        else:
            print(f"❌ ERROR: Unexpected metadata format: {type(data)}")
            return
        
        # Ensure we have matching lengths
        if len(documents) != len(metadatas):
            print(f"⚠️  Mismatch: {len(documents)} documents vs {len(metadatas)} metadata entries")
            # Pad or truncate to match
            min_len = min(len(documents), len(metadatas))
            documents = documents[:min_len]
            metadatas = metadatas[:min_len]
            print(f"✅ Adjusted to {min_len} documents")
        
        _docs_store = []
        for i in range(len(documents)):
            doc_text = documents[i] if i < len(documents) else ""
            doc_meta = metadatas[i] if i < len(metadatas) else {}
            _docs_store.append(_meta_to_doc(i, doc_text, doc_meta, i + 1))
        
        print(f"✅ Loaded {len(_docs_store)} documents into knowledge base")
        
    except Exception as e:
        print(f"❌ Error loading metadata: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Load FAISS index
    if index_path.exists():
        try:
            _vector_index = faiss.read_index(str(index_path))
            print(f"✅ FAISS index loaded: {_vector_index.ntotal} vectors")
        except Exception as e:
            print(f"❌ Error loading FAISS index: {e}")
            _vector_index = None
    else:
        print(f"⚠️  FAISS index not found at {index_path}")
        _vector_index = None
    
    print("✅ Knowledge base initialization complete")
    global _docs_store, _vector_index, _embeddings_model
    meta_path  = FAISS_DIR / "faiss_metadata.pkl"
    index_path = FAISS_DIR / "faiss_index.bin"
    if not meta_path.exists():
        print(f"ERROR: {meta_path} not found"); return
    with open(meta_path, "rb") as f:
        data = pickle.load(f)
    documents = data.get("documents", [])
    metadatas = data.get("metadatas", [])
    _docs_store = [_meta_to_doc(i, documents[i] if i < len(documents) else "",
                                metadatas[i] if i < len(metadatas) else {}, i + 1)
                   for i in range(len(documents))]
    print(f"OK: Loaded {len(_docs_store)} documents")
    if index_path.exists():
        _vector_index = faiss.read_index(str(index_path))
        print(f"OK: FAISS index — {_vector_index.ntotal} vectors")
    print("OK: Knowledge base ready")

# ── Search ────────────────────────────────────────────────────────────

def search_semantic(query: str, top_k: int = 5) -> List[dict]:
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
                doc = dict(_docs_store[idx])
                # Lower L2 distance = more similar; convert to positive relevance
                doc["similarity_score"] = float(distances[0][i])
                doc["_relevance_score"] = max(0.0, 10.0 - float(distances[0][i]))
                results.append(doc)
        return results
    except Exception as e:
        print(f"Semantic search error: {e}"); return []

def search_keyword(query: str, limit: int = 50) -> List[dict]:
    if not _docs_store:
        return []
    q = query.lower()
    words = [w for w in q.split() if len(w) > 2]
    results = []
    for doc in _docs_store:
        score = 0
        title   = doc.get("title",           "").lower()
        preview = doc.get("content_preview", "").lower()
        full    = doc.get("content_full",    "").lower()
        if q in title:   score += 10
        if q in preview: score += 4
        if q in full:    score += 2
        for w in words:
            if w in title:   score += 4
            if w in preview: score += 2
            if w in full:    score += 1
        if score > 0:
            d = dict(doc)
            d["similarity_score"] = min(score / 20.0, 1.0)
            d["_relevance_score"] = float(score)
            results.append(d)
    results.sort(key=lambda x: x["_relevance_score"], reverse=True)
    return results[:limit]

def search_by_title(q: str, limit: int = 5) -> List[dict]:
    q = q.lower().strip()
    results = []
    for doc in _docs_store:
        title = doc.get("title", "").lower()
        if q in title or title in q:
            d = dict(doc)
            d["similarity_score"] = 1.0
            d["_relevance_score"] = 20.0  # exact title match gets highest score
            results.append(d)
    results.sort(key=lambda x: len(x["title"]))
    return results[:limit]

def _deduplicate_and_rank(docs: List[dict]) -> List[dict]:
    """
    Deduplicate by title, then sort by _relevance_score descending
    so the most relevant documents come first.
    """
    seen: set = set()
    unique = []
    for d in docs:
        key = re.sub(r"^\d+\s+", "", d.get("title", "").strip().lower())
        if key and key not in seen:
            seen.add(key)
            unique.append(d)
    # Sort: highest relevance score first
    unique.sort(key=lambda x: x.get("_relevance_score", 0.0), reverse=True)
    return unique

def _expand_query(query: str) -> List[str]:
    expansions = [query]
    q = query.lower()
    core = re.sub(
        r"^(describe|explain|tell me about|what is|what are|how did|how do|"
        r"why did|why do|summarise|summarize|give me information on|"
        r"provide details on|what does the research say about)\s+", "", q
    ).strip()
    if core != q:
        expansions.append(core)

    topic_map = {
        "naval technology":  ["shipbuilding", "ship construction", "treasure ship", "bao chuan", "junk ship", "ming fleet"],
        "ming dynasty":      ["ming", "ming china", "yongle", "ming period"],
        "naval":             ["navy", "maritime", "fleet", "sea power"],
        "technology":        ["technique", "engineering", "design", "method"],
        "ship":              ["vessel", "junk", "treasure ship", "bao chuan"],
        "navigation":        ["compass", "star chart", "celestial navigation", "dead reckoning"],
        "construction":      ["shipyard", "timber", "dry dock"],
        "zheng he":          ["zheng he", "cheng ho", "admiral", "treasure fleet"],
        "calicut":           ["calicut", "kozhikode", "malabar"],
        "malacca":           ["malacca", "melaka", "strait of malacca"],
        "africa":            ["east africa", "mombasa", "malindi", "zanzibar", "mogadishu"],
        "americas":          ["america", "new world", "pre-columbian", "chinese in america"],
        "australia":         ["australia", "aboriginal", "broome", "darwin"],
        "new zealand":       ["new zealand", "maori", "waitaha"],
        "1421":              ["1421 hypothesis", "gavin menzies", "1421 foundation"],
        "1418 map":          ["1418 map", "zheng he map", "liu gang map"],
        "evidence":          ["evidence", "proof", "artefact", "ceramic", "archaeology"],
        "genetics":          ["dna", "genetic", "ancestry", "haplogroup"],
        "europe":            ["europe", "european", "portugal", "venice", "mediterranean"],
        "south america":     ["south america", "peru", "brazil", "chile", "ecuador"],
    }
    for topic, syns in topic_map.items():
        if topic in q or any(w in q for w in topic.split()):
            expansions.extend(syns)

    stop = {"describe","explain","what","how","did","the","and","for","tell","about","give","me","does","say"}
    expansions.extend([w for w in core.split() if len(w) > 4 and w not in stop][:5])
    return list(dict.fromkeys(expansions))


def filter_relevant_sources(sources: List[dict], max_sources: int = 5, relevance_threshold: float = 0.3) -> List[dict]:
    """
    Filter sources to only include relevant ones based on relevance_score.
    
    Args:
        sources: List of source documents with _relevance_score
        max_sources: Maximum number of sources to return (default 5)
        relevance_threshold: Minimum relevance score to keep (0-1 scale)
    
    Returns:
        Filtered list of sources, sorted by relevance (highest first)
    """
    if not sources:
        return []
    
    filtered = []
    for src in sources:
        score = src.get("_relevance_score", 0)
        
        # Normalize score based on type
        # For semantic search: scores are 0-10 (higher is better)
        # For keyword search: scores can be 0-100+
        # For title match: score is 20
        
        # Normalize to 0-1 scale for threshold comparison
        normalized_score = 0
        if score >= 20:  # Title match
            normalized_score = 1.0
        elif score >= 10:  # Very high keyword match
            normalized_score = 0.9
        elif score >= 5:   # Good match
            normalized_score = 0.7
        elif score >= 2:   # Moderate match
            normalized_score = 0.5
        elif score >= 1:   # Low match
            normalized_score = 0.3
        else:
            normalized_score = score / 10 if score < 10 else score / 100
        
        # Keep sources above threshold
        if normalized_score >= relevance_threshold:
            filtered.append(src)
    
    # Also keep at least 1 source if any exist (don't return empty if there are sources)
    if not filtered and sources:
        # Keep the top 1 source even if below threshold
        filtered = [sources[0]]
    
    # Limit to max_sources
    if len(filtered) > max_sources:
        filtered = filtered[:max_sources]
    
    return filtered


def get_relevant_context(query: str, top_k: int = 10) -> tuple:
    """
    Multi-strategy search returning documents ranked by relevance score
    (most relevant first). Returns dynamic number of sources based on relevance.
    """
    docs_by_id: dict = {}
    expanded = _expand_query(query)
    print(f"Query: '{query}' → {len(expanded)} variants")

    # Strategy 1: Semantic search — gives a relevance score per result
    for sq in expanded[:12]:
        for d in search_semantic(sq, top_k):
            did = d["id"]
            if did not in docs_by_id:
                docs_by_id[did] = d
            else:
                # Keep the highest relevance score across multiple searches
                if d["_relevance_score"] > docs_by_id[did]["_relevance_score"]:
                    docs_by_id[did]["_relevance_score"] = d["_relevance_score"]

    # Strategy 2: Keyword search — good for exact term matches
    for d in search_keyword(query, top_k * 2):
        did = d["id"]
        if did not in docs_by_id:
            docs_by_id[did] = d
        else:
            docs_by_id[did]["_relevance_score"] += d["_relevance_score"] * 0.5

    for sq in expanded[1:8]:
        for d in search_keyword(sq, top_k):
            did = d["id"]
            if did not in docs_by_id:
                docs_by_id[did] = d
            else:
                docs_by_id[did]["_relevance_score"] += d["_relevance_score"] * 0.3

    # Strategy 3: Title search
    m = re.search(r'["\'](.+?)["\']', query)
    if m:
        for d in search_by_title(m.group(1)):
            did = d["id"]
            if did not in docs_by_id:
                docs_by_id[did] = d
            else:
                docs_by_id[did]["_relevance_score"] += 20.0

    docs = _deduplicate_and_rank(list(docs_by_id.values()))
    
    # ✅ NEW: Filter to only relevant sources (dynamic, not fixed number)
    relevant_docs = filter_relevant_sources(docs, max_sources=5, relevance_threshold=0.3)
    
    print(f"Found {len(docs)} total docs → {len(relevant_docs)} relevant docs. Top: {[d['title'][:50] for d in relevant_docs[:3]]}")

    if not relevant_docs:
        return "", []

    # Build context with the relevant docs only
    context = "Relevant documents from the 1421 Foundation knowledge base:\n\n"
    for i, doc in enumerate(relevant_docs, 1):
        context += f"[Document {i}] {doc['title']}"
        if doc.get("year") and doc["year"] > 0:
            context += f" ({doc['year']})"
        if doc.get("author") and doc["author"] != "Unknown":
            context += f" by {doc['author']}"
        context += f"\nType: {doc['type']}\n"
        full = doc.get("content_full", doc.get("content_preview", ""))
        if full:
            context += f"{full[:4000]}\n"
        context += "\n"

    return context, relevant_docs


def get_comparative_context(query: str, top_k: int = 12) -> tuple:
    docs_by_id: dict = {}
    q = query.lower()
    for sep in [" to ", " with ", " and ", " versus ", " vs "]:
        parts = q.replace("compare", "").split(sep)
        if len(parts) >= 2:
            for d in search_semantic(parts[0].strip(), top_k // 2) + search_semantic(parts[1].strip(), top_k // 2):
                did = d["id"]
                if did not in docs_by_id:
                    docs_by_id[did] = d
                else:
                    docs_by_id[did]["_relevance_score"] = max(docs_by_id[did]["_relevance_score"], d["_relevance_score"])
            break
    for d in search_semantic(query, top_k) + search_keyword(query, top_k):
        did = d["id"]
        if did not in docs_by_id:
            docs_by_id[did] = d
        else:
            docs_by_id[did]["_relevance_score"] += d["_relevance_score"] * 0.3

    docs = _deduplicate_and_rank(list(docs_by_id.values()))
    
    # ✅ NEW: Filter to only relevant sources for comparative queries too
    relevant_docs = filter_relevant_sources(docs, max_sources=6, relevance_threshold=0.25)
    
    if not relevant_docs:
        return "", []

    context = "Relevant documents from the 1421 Foundation knowledge base:\n\n"
    for i, doc in enumerate(relevant_docs, 1):
        context += f"[Document {i}] {doc['title']}"
        if doc.get("year") and doc["year"] > 0:
            context += f" ({doc['year']})"
        if doc.get("author") and doc["author"] != "Unknown":
            context += f" by {doc['author']}"
        context += f"\nType: {doc['type']}\n"
        full = doc.get("content_full", doc.get("content_preview", ""))
        if full:
            context += f"{full[:3000]}\n"
        context += "\n"
    return context, relevant_docs

# ── Routes ────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "docs_loaded": len(_docs_store)}

@app.get("/api/locations")
def get_locations(max_year: int = 1433):
    return [loc for loc in VOYAGE_LOCATIONS if loc["year"] <= max_year]

@app.get("/api/documents")
async def get_documents(limit: int = Query(default=10000, le=10000), offset: int = 0):
    if not _docs_store:
        return {"documents": [], "total": 0, "limit": limit, "offset": offset}
    paged = _docs_store[offset: offset + limit]
    safe  = [{k: v for k, v in d.items() if k not in ("content_full", "_relevance_score")} for d in paged]
    return {"documents": safe, "total": len(_docs_store), "limit": limit, "offset": offset}

@app.get("/api/documents/search")
async def search_documents_endpoint(q: str, limit: int = 50):
    results = []
    seen: set = set()
    if q.strip().isdigit():
        for d in _docs_store:
            if d["id"] == q.strip():
                exact = dict(d); exact["similarity_score"] = 1.0
                results.append(exact); seen.add(d["id"]); break
    for d in search_by_title(q, 5):
        if d["id"] not in seen: results.append(d); seen.add(d["id"])
    for d in search_semantic(q, min(limit, 10)):
        if d["id"] not in seen: results.append(d); seen.add(d["id"])
    for d in search_keyword(q, limit):
        if d["id"] not in seen: results.append(d); seen.add(d["id"])
    final = [{k: v for k, v in d.items() if k not in ("content_full", "_relevance_score")} for d in results[:limit]]
    return {"results": final, "total": len(final), "query": q}

@app.get("/api/documents/{doc_id}")
async def get_document_by_id(doc_id: str):
    for d in _docs_store:
        if d["id"] == doc_id:
            return {k: v for k, v in d.items() if k not in ("content_full", "_relevance_score")}
    raise HTTPException(status_code=404, detail="Document not found")

@app.get("/api/documents/types")
async def get_document_types():
    return {"types": sorted({d["type"] for d in _docs_store if d["type"] and d["type"] != "unknown"})}

@app.get("/api/documents/years")
async def get_document_years():
    return {"years": sorted({d["year"] for d in _docs_store if d["year"] and d["year"] > 0}, reverse=True)}

@app.get("/api/documents/authors")
async def get_document_authors():
    return {"authors": sorted({d["author"] for d in _docs_store if d["author"] and d["author"] != "Unknown"})}

def _build_system(context: str, use_web_fallback: bool) -> str:
    if use_web_fallback:
        return SYSTEM_PROMPT_WEB_FALLBACK
    s = SYSTEM_PROMPT_WITH_DOCS + "\n\nDOCUMENTS PROVIDED (most relevant first):\n\n" + context
    s += (
        "\n\nINSTRUCTIONS:\n"
        "- Cite [Document X] after every claim from the documents.\n"
        "- When using your own general knowledge rather than a document, add (general knowledge) inline.\n"
        "- Synthesize across documents for a complete answer.\n"
        "- Structure with clear paragraphs.\n"
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

@app.post("/api/chat")
async def chat(req: ChatRequest):
    llm  = get_llm()
    last = next((m["content"] for m in reversed(req.messages) if m["role"] == "user"), "")
    context, sources = "", []
    used_web_fallback = False

    if req.use_documents and last:
        comparative = ["compare", "versus", "vs", "difference between", "contrast"]
        if any(kw in last.lower() for kw in comparative):
            context, sources = get_comparative_context(last, top_k=12)
        else:
            context, sources = get_relevant_context(last, top_k=10)

    if not sources:
        used_web_fallback = True

    try:
        response = llm.invoke(_to_lc(_build_system(context, used_web_fallback), req.messages))
        # Sources are already filtered and ranked by relevance from get_relevant_context
        clean_sources = [
            {
                "title":           d["title"],
                "author":          d["author"],
                "year":            d["year"],
                "type":            d["type"],
                "relevance_score": round(d.get("_relevance_score", 0.0), 2),
            }
            for d in sources
        ]
        return ChatResponse(
            content=response.content,
            session_id=req.session_id or datetime.now().isoformat(),
            sources=clean_sources if clean_sources else None,
            used_web_fallback=used_web_fallback,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    llm  = get_llm()
    last = next((m["content"] for m in reversed(req.messages) if m["role"] == "user"), "")
    context = ""
    if req.use_documents and last:
        context, _ = get_relevant_context(last, top_k=10)
    lc_messages = _to_lc(_build_system(context, not bool(context)), req.messages)
    async def generate():
        try:
            async for chunk in llm.astream(lc_messages):
                if chunk.content:
                    yield f"data: {chunk.content.replace(chr(10), chr(92)+'n')}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: ERROR: {str(e)}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream",
        headers={"Access-Control-Allow-Origin": VERCEL_ORIGIN,
                 "Access-Control-Allow-Credentials": "true",
                 "Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.get("/api/debug/rag")
async def debug_rag(q: str = "Ming dynasty naval technology"):
    context, docs = get_relevant_context(q, top_k=10)
    return {"query": q, "docs_found": len(docs),
            "ranked_docs": [{"rank": i+1, "title": d["title"], "score": round(d.get("_relevance_score",0),2)}
                            for i, d in enumerate(docs)],
            "faiss_loaded": _vector_index is not None,
            "store_size": len(_docs_store)}

@app.post("/api/feedback")
async def submit_feedback(req: FeedbackRequest):
    import asyncio, concurrent.futures
    feedback_path = DATA_DIR / "feedback.json"
    try:
        existing = json.load(open(feedback_path)) if feedback_path.exists() else []
        existing.append({"name": req.name or "Anonymous", "email": req.email,
                          "feedback_type": req.feedback_type, "message": req.message,
                          "created_at": datetime.now().isoformat()})
        json.dump(existing, open(feedback_path, "w"), indent=2)
    except Exception as e:
        print(f"Feedback store error: {e}")
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        loop.run_in_executor(pool, send_feedback_email, req.name or "Anonymous",
                             req.email, req.feedback_type, req.message)
    return {"status": "ok"}

@app.get("/api/stats")
def get_stats():
    feedback_count = 0
    try:
        fp = DATA_DIR / "feedback.json"
        if fp.exists():
            feedback_count = len(json.load(open(fp)))
    except Exception:
        pass
    return {"feedback_count": feedback_count, "locations_count": len(VOYAGE_LOCATIONS),
            "documents_count": len(_docs_store) or 347}

@app.get("/api/test-db")
async def test_db():
    return {"store_size": len(_docs_store),
            "faiss_loaded": _vector_index is not None,
            "faiss_vectors": _vector_index.ntotal if _vector_index else 0,
            "sample": [{"id": d["id"], "title": d["title"]} for d in _docs_store[:5]]}

@app.on_event("startup")
def init_app():
    print(f"DATA_DIR: {DATA_DIR} (exists={DATA_DIR.exists()})")
    load_knowledge_base()