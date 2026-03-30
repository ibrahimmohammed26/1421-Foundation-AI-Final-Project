"""
1421 Foundation Research System - FastAPI Backend
"""

import os
import pickle
import resend
import json
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
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

# ── Email config ──────────────────────────────────────────────────────
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
NOTIFY_EMAIL   = os.getenv("NOTIFY_EMAIL",  "")

def send_feedback_email(name: str, email: str, feedback_type: str, message: str):
    if not RESEND_API_KEY:
        print("WARNING: RESEND_API_KEY not set — skipping email")
        return
    try:
        resend.api_key = RESEND_API_KEY
        to_addr = NOTIFY_EMAIL if NOTIFY_EMAIL else "ibrahimalim2605@gmail.com"
        r = resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": to_addr,
            "subject": f"[1421 Foundation] New Feedback: {feedback_type}",
            "html": f"""
                <h2 style="color:#8B0000;">New Feedback - 1421 Foundation Research System</h2>
                <table style="font-family:Arial,sans-serif;font-size:14px;border-collapse:collapse;">
                    <tr><td style="padding:6px 12px;font-weight:bold;">Name</td><td style="padding:6px 12px;">{name}</td></tr>
                    <tr><td style="padding:6px 12px;font-weight:bold;">Email</td><td style="padding:6px 12px;">{email}</td></tr>
                    <tr><td style="padding:6px 12px;font-weight:bold;">Type</td><td style="padding:6px 12px;">{feedback_type}</td></tr>
                    <tr><td style="padding:6px 12px;font-weight:bold;">Date</td><td style="padding:6px 12px;">{datetime.now().strftime("%d %b %Y %H:%M")}</td></tr>
                </table>
                <h3 style="color:#8B0000;">Message</h3>
                <p style="font-family:Arial,sans-serif;font-size:14px;background:#f9f9f9;padding:12px;border-left:4px solid #8B0000;">{message}</p>
                <hr/>
                <p style="font-size:12px;color:#999;">Sent from 1421 Foundation Research System</p>
            """
        })
        print(f"OK: Feedback email sent via Resend, id={r.get('id', '?')}")
    except Exception as e:
        print(f"ERROR: Resend email failed: {e}")

# ── LLM ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a research assistant for the 1421 Foundation, specialising in Chinese maritime exploration during the Ming dynasty (1368–1644), particularly the voyages of Admiral Zheng He and the 1421 hypothesis by Gavin Menzies.

IMPORTANT RULES — READ CAREFULLY:
1. You answer based on the documents provided to you in this prompt. Do NOT use external knowledge or web searches.

2. **YOU CAN INFER AND SYNTHESIZE**: Use the provided documents to answer questions. If multiple documents contain related information, combine them to form a complete answer. You don't need an exact match.

3. For descriptive questions like "Describe X" or "Explain Y":
   - Look for documents that contain information about the topic
   - Synthesize information from multiple documents
   - Organize your answer by key aspects (e.g., ship types, navigation methods, weapons, construction)

4. Every claim must cite its source using [Document X] inline.

5. Only if NO documents contain ANY relevant information, respond with:
   "No data source found in the 1421 Foundation knowledge base for this query. Please try a different search term or browse the Documents section directly."

6. Write in clear, academic UK English. Structure your response with clear headings or paragraphs.

7. Be specific and factual. If the documents mention specific ship names, dimensions, or dates, include them."""
def get_comparative_context(query: str, top_k: int = 10) -> tuple:
    """Special handling for comparative questions"""
    docs = []
    seen_ids = set()
    
    # Extract the two things being compared
    q_lower = query.lower()
    
    # For "compare X to Y" queries
    compare_parts = None
    if "compare" in q_lower:
        parts = q_lower.split("compare")
        if len(parts) > 1:
            rest = parts[1].replace("to", "and").replace("with", "and").replace("versus", "and").replace("vs", "and")
            compare_parts = [p.strip() for p in rest.split("and") if p.strip()]
    
    # Search for each part separately
    if compare_parts and len(compare_parts) >= 2:
        part1_results = search_semantic(compare_parts[0], top_k // 2)
        part2_results = search_semantic(compare_parts[1], top_k // 2)
        
        for d in part1_results + part2_results:
            if d["id"] not in seen_ids:
                docs.append(d)
                seen_ids.add(d["id"])
    
    # Also search the full query
    full_results = search_semantic(query, top_k)
    for d in full_results:
        if d["id"] not in seen_ids:
            docs.append(d)
            seen_ids.add(d["id"])
    
    # If still not enough, try keyword search
    if len(docs) < 4:
        keyword_results = search_keyword(query, top_k)
        for d in keyword_results:
            if d["id"] not in seen_ids:
                docs.append(d)
                seen_ids.add(d["id"])
    
    # Deduplicate
    seen_titles = set()
    unique_docs = []
    for d in docs:
        t = d.get("title", "").strip().lower()
        if t and t not in seen_titles:
            seen_titles.add(t)
            unique_docs.append(d)
    
    if not unique_docs:
        return "", []
    
    context = "Relevant documents from the 1421 Foundation knowledge base:\n\n"
    for i, doc in enumerate(unique_docs[:top_k], 1):
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
    
    return context, unique_docs[:top_k]

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
    {"name": "Nanjing",    "lat": 32.06,  "lon": 118.80, "year": 1403, "event": "Yongle Emperor commissions the treasure fleet from Nanjing"},
    {"name": "Nanjing",    "lat": 32.06,  "lon": 118.80, "year": 1405, "event": "First voyage departs — 317 ships and 28,000 men set sail"},
    {"name": "Champa",     "lat": 10.82,  "lon": 106.63, "year": 1405, "event": "First stop on Voyage 1 — Southeast Asian ally (modern Vietnam)"},
    {"name": "Java",       "lat": -7.61,  "lon": 110.71, "year": 1406, "event": "Voyage 1 — diplomatic missions conducted on Java"},
    {"name": "Sumatra",    "lat": -0.59,  "lon": 101.34, "year": 1406, "event": "Voyage 1 — strategic trading post established at Palembang"},
    {"name": "Malacca",    "lat":  2.19,  "lon": 102.25, "year": 1406, "event": "Voyage 1 — key port established, local piracy suppressed"},
    {"name": "Calicut",    "lat": 11.26,  "lon":  75.78, "year": 1407, "event": "Voyage 1 — primary destination on the Malabar Coast, India"},
    {"name": "Siam",       "lat": 13.74,  "lon": 100.52, "year": 1408, "event": "Voyage 2 — diplomatic relations established (modern Thailand)"},
    {"name": "Sri Lanka",  "lat":  7.87,  "lon":  80.77, "year": 1409, "event": "Voyage 2 — trilingual inscription erected at Galle"},
    {"name": "Hormuz",     "lat": 27.16,  "lon":  56.28, "year": 1414, "event": "Voyage 4 — Persian Gulf reached for first time, 18 states sent tribute"},
    {"name": "Aden",       "lat": 12.79,  "lon":  45.02, "year": 1417, "event": "Voyage 5 — Arabian Peninsula reached, gifts of zebras and lions received"},
    {"name": "Mogadishu",  "lat":  2.05,  "lon":  45.32, "year": 1418, "event": "Voyage 5 — Somali coast, first Chinese fleet to reach East Africa"},
    {"name": "Malindi",    "lat": -3.22,  "lon":  40.12, "year": 1418, "event": "Voyage 5 — Kenya coast, famous giraffe gifted to the Yongle Emperor"},
    {"name": "Mombasa",    "lat": -4.04,  "lon":  39.67, "year": 1419, "event": "Voyage 5 — East African trade firmly established"},
    {"name": "Zanzibar",   "lat": -6.17,  "lon":  39.20, "year": 1421, "event": "Voyage 6 — southernmost point of the treasure fleet voyages"},
    {"name": "Jidda",      "lat": 21.49,  "lon":  39.19, "year": 1432, "event": "Voyage 7 — Red Sea reached, auxiliary fleet sent towards Mecca"},
    {"name": "Calicut",    "lat": 11.26,  "lon":  75.78, "year": 1433, "event": "Voyage 7 — Zheng He dies here on the return journey, ending the voyages"},
]

# ── Document store ────────────────────────────────────────────────────

_docs_store: List[dict] = []
_vector_index = None
_embeddings_model = None

def _clean_text(text: str) -> str:
    import re
    lines = text.split("\n")
    cleaned = []
    strip_label_prefixes = ("Title:", "Author:", "Source:", "Type:", "Tags:")
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
        for prefix in strip_label_prefixes:
            if stripped.startswith(prefix):
                value = stripped[len(prefix):].strip()
                if prefix == "Source:" and value:
                    cleaned.append(value)
                matched = True
                break
        if not matched:
            cleaned.append(stripped)
    result = " ".join(cleaned)
    result = re.sub(r"  +", " ", result)
    return result.strip()

def _meta_to_doc(idx: int, text: str, meta: dict, doc_id) -> dict:
    clean = _clean_text(text)
    raw_title = meta.get("title", "") or ""
    title = raw_title.strip()
    for line in text.split("\n"):
        stripped_line = line.strip()
        if stripped_line.lower().startswith("title:"):
            candidate = stripped_line[6:].strip()
            if len(candidate) > len(title):
                title = candidate
            break
    if not title:
        first = clean.split(".")[0].strip()
        title = first[:200] if first else f"Document {idx+1}"
    author = meta.get("author", "Unknown") or "Unknown"
    return {
        "id":               str(doc_id),
        "title":            title,
        "author":           author,
        "year":             int(meta.get("year", 0) or 0),
        "type":             meta.get("source_type", meta.get("type", "document")) or "document",
        "description":      clean,
        "tags":             meta.get("tags", []) or [],
        "content_preview":  clean,
        "content_full":     clean,
        "source_file":      meta.get("source_file", meta.get("source", meta.get("source_type", ""))) or "",
        "url":              meta.get("url", "") or "",
        "page_number":      meta.get("page", None),
        "similarity_score": None,
    }

def load_knowledge_base():
    global _docs_store, _vector_index, _embeddings_model
    meta_path  = FAISS_DIR / "faiss_metadata.pkl"
    index_path = FAISS_DIR / "faiss_index.bin"
    if not meta_path.exists():
        print(f"ERROR: {meta_path} not found")
        return
    with open(meta_path, "rb") as f:
        data = pickle.load(f)
    documents = data.get("documents", [])
    metadatas = data.get("metadatas", [])
    _docs_store = []
    for i in range(len(documents)):
        text = documents[i] if i < len(documents) else ""
        meta = metadatas[i] if i < len(metadatas) else {}
        did  = i + 1
        _docs_store.append(_meta_to_doc(i, text, meta, did))
    print(f"OK: Loaded {len(_docs_store)} documents from pickle")
    if index_path.exists():
        _vector_index = faiss.read_index(str(index_path))
        print(f"OK: Loaded FAISS index with {_vector_index.ntotal} vectors")
    else:
        print(f"WARNING: FAISS index not found at {index_path}")
    print("OK: Knowledge base ready")

# ── Search ────────────────────────────────────────────────────────────

def search_semantic(query: str, top_k: int = 5) -> List[dict]:
    global _embeddings_model
    if _vector_index is None or not _docs_store:
        return []
    try:
        if _embeddings_model is None:
            _embeddings_model = get_embeddings_fn()
    except Exception as e:
        print(f"WARNING: Could not init embeddings model: {e}")
        return []
    try:
        vec = np.array([_embeddings_model.embed_query(query)], dtype="float32")
        distances, indices = _vector_index.search(vec, min(top_k, _vector_index.ntotal))
        results = []
        for i, idx in enumerate(indices[0]):
            if 0 <= idx < len(_docs_store):
                doc = dict(_docs_store[idx])
                doc["similarity_score"] = float(distances[0][i])
                results.append(doc)
        return results
    except Exception as e:
        print(f"ERROR semantic search: {e}")
        return []

def search_keyword(query: str, limit: int = 50) -> List[dict]:
    if not _docs_store:
        return []
    q = query.lower()
    words = [w for w in q.split() if len(w) > 2]
    results = []
    for doc in _docs_store:
        score   = 0
        title   = doc.get("title",           "").lower()
        author  = doc.get("author",          "").lower()
        preview = doc.get("content_preview", "").lower()
        full    = doc.get("content_full",    "").lower()
        if q in title:   score += 5
        if q in author:  score += 3
        if q in preview: score += 2
        if q in full:    score += 1
        for w in words:
            if w in title:   score += 2
            if w in preview: score += 1
        if score > 0:
            d = dict(doc)
            d["similarity_score"] = min(score / 10.0, 1.0)
            results.append(d)
    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return results[:limit]

def search_by_title(title_query: str, limit: int = 5) -> List[dict]:
    q = title_query.lower().strip()
    results = []
    for doc in _docs_store:
        title = doc.get("title", "").lower()
        if q in title or title in q:
            d = dict(doc)
            d["similarity_score"] = 1.0
            results.append(d)
    results.sort(key=lambda x: len(x["title"]))
    return results[:limit]

def get_relevant_context(query: str, top_k: int = 10) -> tuple:
    """Enhanced context retrieval with better search for technical/historical queries"""
    docs = []
    seen_ids = set()
    import re
    
    # Expand query with related terms for better retrieval
    def expand_query(q: str) -> List[str]:
        expansions = [q]
        q_lower = q.lower()
        
        # Remove common question phrases
        clean_q = re.sub(r'^(describe|explain|tell me about|what is|what are|how did|how do|why did|why do)\s+', '', q_lower)
        expansions.append(clean_q)
        
        # Technical term expansions for naval/military topics
        topic_expansions = {
            "naval technology": ["shipbuilding", "naval architecture", "marine engineering", "warship design", "treasure ship", "junk ship"],
            "ming dynasty": ["ming", "ming china", "chinese empire", "ming period"],
            "naval": ["navy", "maritime", "sea", "ocean", "fleet", "armada"],
            "technology": ["technique", "innovation", "invention", "method", "design", "engineering"],
            "ship": ["vessel", "boat", "junk", "craft", "treasure ship", "bao chuan"],
            "weapon": ["cannon", "gunpowder", "armament", "military"],
            "navigation": ["compass", "chart", "star chart", "sextant", "dead reckoning", "celestial navigation"],
            "construction": ["building", "building techniques", "shipyard", "dry dock", "timber"],
        }
        
        # Add expansions for topic keywords found in query
        for topic, expansions_list in topic_expansions.items():
            if topic in q_lower or any(word in q_lower for word in topic.split()):
                for exp in expansions_list:
                    expansions.append(exp)
        
        # Add keyword variations
        words = q_lower.split()
        if len(words) > 1:
            # Add bigrams
            for i in range(len(words)-1):
                bigram = f"{words[i]} {words[i+1]}"
                if bigram not in expansions:
                    expansions.append(bigram)
        
        return list(set(expansions))  # Remove duplicates
    
    # Try multiple search strategies with expanded queries
    expanded_queries = expand_query(query)
    
    # Strategy 1: Semantic search with each expanded query
    for sq in expanded_queries[:5]:  # Try up to 5 variations
        try:
            semantic_results = search_semantic(sq, top_k)
            for d in semantic_results:
                if d["id"] not in seen_ids:
                    docs.append(d)
                    seen_ids.add(d["id"])
        except Exception as e:
            print(f"Semantic search error for '{sq}': {e}")
    
    # Strategy 2: Keyword search (good for technical terms)
    keyword_results = search_keyword(query, top_k)
    for d in keyword_results:
        if d["id"] not in seen_ids:
            docs.append(d)
            seen_ids.add(d["id"])
    
    # Strategy 3: If still no results, try searching for individual keywords
    if len(docs) < 3:
        keywords = [w for w in query.lower().split() if len(w) > 3]
        for kw in keywords[:5]:
            kw_results = search_keyword(kw, top_k)
            for d in kw_results:
                if d["id"] not in seen_ids:
                    docs.append(d)
                    seen_ids.add(d["id"])
    
    # Strategy 4: Title-based search for specific documents
    title_patterns = [
        r'(?:article|document|paper|report|piece|post|about|called|titled|named|on)\s+["\']?(.+?)["\']?$',
        r'(?:describe|explain|tell me about|what is|what are)\s+["\'](.+?)["\']',
    ]
    title_hit = None
    for pattern in title_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            title_hit = match.group(1).strip()
            break
    if title_hit:
        for d in search_by_title(title_hit):
            if d["id"] not in seen_ids:
                docs.append(d)
                seen_ids.add(d["id"])
    
    # Deduplicate by title to avoid showing the same document multiple times
    seen_titles: set = set()
    unique_docs = []
    for d in docs:
        t = d.get("title", "").strip().lower()
        # Remove document number prefixes for better deduplication
        t_clean = re.sub(r'^\d+\s+', '', t)
        key = t_clean or t
        if key and key not in seen_titles:
            seen_titles.add(key)
            unique_docs.append(d)
    
    docs = unique_docs
    
    # Log what was found for debugging
    print(f"Query: '{query}' -> Found {len(docs)} documents")
    if docs:
        print(f"Top docs: {[d['title'][:50] for d in docs[:3]]}")
    
    if not docs:
        return "", []
    
    # Build context with more content from each document
    context = "Relevant documents from the 1421 Foundation knowledge base:\n\n"
    for i, doc in enumerate(docs[:top_k], 1):
        context += f"[Document {i}] {doc['title']}"
        if doc.get("year") and doc["year"] > 0:
            context += f" ({doc['year']})"
        if doc.get("author") and doc["author"] != "Unknown":
            context += f" by {doc['author']}"
        context += f"\nType: {doc['type']}\n"
        
        # Use full content if available, otherwise preview
        full = doc.get("content_full", doc.get("content_preview", ""))
        if full:
            # Increased from 2000 to 4000 characters for better context
            context += f"{full[:4000]}\n"
        
        if doc.get("tags"):
            context += f"Tags: {', '.join(doc['tags'])}\n"
        context += "\n"
    
    return context, docs[:top_k]
    docs = []
    seen_ids = set()
    import re
    
    # Expand query with related terms for better retrieval
    def expand_query(q: str) -> List[str]:
        expansions = [q]
        q_lower = q.lower()
        
        # Add comparative search terms
        if "compare" in q_lower or "versus" in q_lower or "vs" in q_lower:
            expansions.append(q.replace("compare", "difference between"))
            expansions.append(q.replace("compare", "contrast"))
        
        # Add navigation-related expansions
        if "navigation" in q_lower:
            expansions.extend([
                q.replace("navigation", "ship technology"),
                q.replace("navigation", "seafaring"),
                q.replace("navigation", "maritime techniques"),
                q.replace("navigation", "sailing methods")
            ])
        
        # Add Chinese-specific expansions
        if "chinese" in q_lower:
            expansions.extend([
                q.replace("chinese", "Ming dynasty"),
                q.replace("chinese", "Zheng He"),
                q.replace("chinese", "Chinese fleet"),
                q.replace("chinese", "treasure ships")
            ])
        
        # Add European-specific expansions  
        if "european" in q_lower:
            expansions.extend([
                q.replace("european", "Western"),
                q.replace("european", "Portuguese"),
                q.replace("european", "Spanish"),
                q.replace("european", "Columbus")
            ])
        
        return list(set(expansions))  # Remove duplicates
    
    # Try multiple search strategies
    search_queries = expand_query(query)
    
    for sq in search_queries[:3]:  # Limit to 3 variations to avoid too many API calls
        # Semantic search with lower threshold
        semantic_results = search_semantic(sq, top_k)
        for d in semantic_results:
            if d["id"] not in seen_ids:
                docs.append(d)
                seen_ids.add(d["id"])
        
        # Keyword search as backup
        keyword_results = search_keyword(sq, top_k)
        for d in keyword_results:
            if d["id"] not in seen_ids:
                docs.append(d)
                seen_ids.add(d["id"])
    
    # Try title-based search if we still don't have enough docs
    if len(docs) < 3:
        title_patterns = [
            r'(?:article|document|paper|report|piece|post)\s+(?:about|called|titled|named|on)\s+["\']?(.+?)["\']?$',
            r'(?:tell me about|summarise|summarize|what does|what is in|explain)\s+["\'](.+?)["\']',
            r'["\'](.+?)["\']',
        ]
        title_hit = None
        for pattern in title_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                title_hit = match.group(1).strip()
                break
        if title_hit:
            for d in search_by_title(title_hit):
                if d["id"] not in seen_ids:
                    docs.append(d)
                    seen_ids.add(d["id"])
    
    # Deduplicate by title
    import re as _re
    seen_titles: set = set()
    unique_docs = []
    for d in docs:
        t = d.get("title", "").strip().lower()
        t_norm = _re.sub(r"^\d+\s+", "", t).strip()
        key = t_norm or t
        if key and key not in seen_titles:
            seen_titles.add(key)
            unique_docs.append(d)
    docs = unique_docs
    
    if not docs:
        return "", []
    
    context = "Relevant documents from the 1421 Foundation knowledge base:\n\n"
    for i, doc in enumerate(docs[:top_k], 1):
        context += f"[Document {i}] {doc['title']}"
        if doc.get("year") and doc["year"] > 0:
            context += f" ({doc['year']})"
        if doc.get("author") and doc["author"] != "Unknown":
            context += f" by {doc['author']}"
        context += f"\nType: {doc['type']}\n"
        full = doc.get("content_full", doc.get("content_preview", ""))
        if full:
            # Include more content for better context
            context += f"{full[:3000]}\n"  # Increased from 2000 to 3000
        if doc.get("tags"):
            context += f"Tags: {', '.join(doc['tags'])}\n"
        context += "\n"
    
    return context, docs[:top_k]
    docs = []
    seen_ids = set()
    import re
    title_patterns = [
        r'(?:article|document|paper|report|piece|post)\s+(?:about|called|titled|named|on)\s+["\']?(.+?)["\']?$',
        r'(?:tell me about|summarise|summarize|what does|what is in|explain)\s+["\'](.+?)["\']',
        r'["\'](.+?)["\']',
    ]
    title_hit = None
    for pattern in title_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            title_hit = match.group(1).strip()
            break
    if title_hit:
        for d in search_by_title(title_hit):
            if d["id"] not in seen_ids:
                docs.append(d)
                seen_ids.add(d["id"])
    for d in search_semantic(query, top_k):
        if d["id"] not in seen_ids:
            docs.append(d)
            seen_ids.add(d["id"])
    if not docs:
        for d in search_keyword(query, top_k):
            if d["id"] not in seen_ids:
                docs.append(d)
                seen_ids.add(d["id"])
    import re as _re
    seen_titles: set = set()
    unique_docs = []
    for d in docs:
        t = d.get("title", "").strip().lower()
        t_norm = _re.sub(r"^\d+\s+", "", t).strip()
        key = t_norm or t
        if key and key not in seen_titles:
            seen_titles.add(key)
            unique_docs.append(d)
    docs = unique_docs
    if not docs:
        return "", []
    context = "Relevant documents from the 1421 Foundation knowledge base:\n\n"
    for i, doc in enumerate(docs[:top_k], 1):
        context += f"[Document {i}] {doc['title']}"
        if doc.get("year") and doc["year"] > 0:
            context += f" ({doc['year']})"
        if doc.get("author") and doc["author"] != "Unknown":
            context += f" by {doc['author']}"
        context += f"\nType: {doc['type']}\n"
        full = doc.get("content_full", doc.get("content_preview", ""))
        if full:
            context += f"{full[:2000]}\n"
        if doc.get("tags"):
            context += f"Tags: {', '.join(doc['tags'])}\n"
        context += "\n"
    return context, docs[:top_k]

# ── Routes ────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "service": "1421 Foundation API", "docs_loaded": len(_docs_store)}

@app.get("/api/locations")
def get_locations(max_year: int = 1433):
    return [loc for loc in VOYAGE_LOCATIONS if loc["year"] <= max_year]

@app.get("/api/documents")
async def get_documents(limit: int = Query(default=500, le=10000), offset: int = 0):
    if not _docs_store:
        return {"documents": [], "total": 0, "limit": limit, "offset": offset}
    total = len(_docs_store)
    paged = _docs_store[offset: offset + limit]
    safe  = [{k: v for k, v in d.items() if k != "content_full"} for d in paged]
    return {"documents": safe, "total": total, "limit": limit, "offset": offset}

@app.get("/api/documents/search")
async def search_documents_endpoint(q: str, limit: int = 50):
    results = []
    seen = set()
    if q.strip().isdigit():
        target_id = q.strip()
        for d in _docs_store:
            if d["id"] == target_id:
                exact = dict(d)
                exact["similarity_score"] = 1.0
                results.append(exact)
                seen.add(d["id"])
                break
    for d in search_by_title(q, 5):
        if d["id"] not in seen:
            results.append(d)
            seen.add(d["id"])
    for d in search_semantic(q, min(limit, 10)):
        if d["id"] not in seen:
            results.append(d)
            seen.add(d["id"])
    for d in search_keyword(q, limit):
        if d["id"] not in seen:
            results.append(d)
            seen.add(d["id"])
    final = [{k: v for k, v in d.items() if k != "content_full"} for d in results[:limit]]
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
    authors = sorted({d["author"] for d in _docs_store if d["author"] and d["author"] != "Unknown"})
    return {"authors": authors}

def _build_system(context: str) -> str:
    s = SYSTEM_PROMPT + "\n\n"
    if context:
        s += "DOCUMENTS PROVIDED FOR THIS QUERY:\n\n"
        s += context
        s += (
            "\nINSTRUCTIONS FOR YOUR RESPONSE:\n"
            "- Answer ONLY from the documents above. Do not use outside knowledge.\n"
            "- After every sentence or point of evidence, add [Document X] inline.\n"
            "- If multiple documents support a point, cite all: [Document 1][Document 2].\n"
            "- Structure your answer in clear paragraphs.\n"
            "- If the documents do not contain enough information to answer, say so explicitly.\n"
        )
    else:
        s += (
            "NO DOCUMENTS FOUND FOR THIS QUERY.\n\n"
            "You must respond with exactly this message:\n"
            "'No data source found in the 1421 Foundation knowledge base for this query. "
            "Please try a different search term or browse the Documents section directly.'\n"
            "Do not add anything else."
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
    
    if req.use_documents and last:
        # Check if this is a comparative question
        comparative_keywords = ["compare", "versus", "vs", "difference between", "contrast"]
        is_comparative = any(kw in last.lower() for kw in comparative_keywords)
        
        if is_comparative:
            # Use specialized comparative retrieval
            context, sources = get_comparative_context(last, top_k=10)
        else:
            # Use standard retrieval
            context, sources = get_relevant_context(last, top_k=8)
    
    try:
        response = llm.invoke(_to_lc(_build_system(context), req.messages))
        
        # Clean up similarity scores before sending to frontend
        clean_sources = []
        for d in sources:
            clean_source = {
                "title":  d["title"],
                "author": d["author"],
                "year":   d["year"],
                "type":   d["type"],
                # Remove similarity to avoid showing percentages
            }
            clean_sources.append(clean_source)
        
        return ChatResponse(
            content=response.content,
            session_id=req.session_id or datetime.now().isoformat(),
            sources=clean_sources if clean_sources else None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    llm  = get_llm()
    last = next((m["content"] for m in reversed(req.messages) if m["role"] == "user"), "")
    context, sources = "", []
    if req.use_documents and last:
        context, sources = get_relevant_context(last, top_k=8)
    try:
        response = llm.invoke(_to_lc(_build_system(context), req.messages))
        return ChatResponse(
            content=response.content,
            session_id=req.session_id or datetime.now().isoformat(),
            sources=[{
                "title":      d["title"],
                "author":     d["author"],
                "year":       d["year"],
                "type":       d["type"],
                "similarity": d.get("similarity_score"),
            } for d in sources] or None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    llm  = get_llm()
    last = next((m["content"] for m in reversed(req.messages) if m["role"] == "user"), "")
    context = ""
    if req.use_documents and last:
        context, _ = get_relevant_context(last, top_k=8)
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
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Access-Control-Allow-Origin": VERCEL_ORIGIN,
            "Access-Control-Allow-Credentials": "true",
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )

@app.get("/api/debug/rag")
async def debug_rag(q: str = "Zheng He voyages"):
    context, docs = get_relevant_context(q, top_k=8)
    return {
        "query":           q,
        "docs_found":      len(docs),
        "doc_titles":      [d["title"] for d in docs],
        "faiss_loaded":    _vector_index is not None,
        "faiss_vectors":   _vector_index.ntotal if _vector_index else 0,
        "store_size":      len(_docs_store),
        "context_preview": context[:2000] if context else "(empty)",
    }

@app.post("/api/feedback")
async def submit_feedback(req: FeedbackRequest):
    import asyncio, concurrent.futures
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
        print("Feedback saved to file OK")
    except Exception as e:
        print(f"Feedback store error: {e}")
    print(f"RESEND_API_KEY set: {bool(RESEND_API_KEY)}")
    print(f"NOTIFY_EMAIL set: {bool(NOTIFY_EMAIL)}, value: {NOTIFY_EMAIL or 'EMPTY'}")
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        loop.run_in_executor(pool, send_feedback_email, req.name or "Anonymous", req.email, req.feedback_type, req.message)
    return {"status": "ok", "message": "Feedback received"}

@app.get("/api/stats")
def get_stats():
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

@app.get("/api/test-db")
async def test_db():
    sample = [{"id": d["id"], "title": d["title"]} for d in _docs_store[:5]]
    return {
        "store_size":    len(_docs_store),
        "faiss_loaded":  _vector_index is not None,
        "faiss_vectors": _vector_index.ntotal if _vector_index else 0,
        "sample":        sample,
    }

@app.on_event("startup")
def init_app():
    print(f"BASE_DIR : {BASE_DIR}")
    print(f"DATA_DIR : {DATA_DIR}  (exists={DATA_DIR.exists()})")
    print(f"Email configured: {bool(RESEND_API_KEY)}")
    load_knowledge_base()