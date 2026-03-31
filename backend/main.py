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

# ── Email config ──────────────────────────────────────────────────────
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
NOTIFY_EMAIL   = os.getenv("NOTIFY_EMAIL", "")

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
                <table style="font-family:Arial,sans-serif;font-size:14px;">
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

IMPORTANT RULES:
1. Answer ONLY from the documents provided. Do NOT use external knowledge or web searches.
2. YOU CAN INFER AND SYNTHESIZE: Combine information from multiple documents to form a complete answer. You do not need an exact match — use related documents to build a comprehensive response.
3. Every claim MUST cite its source inline using [Document X] immediately after the relevant sentence.
4. If multiple documents support a point, cite all: [Document 1][Document 2].
5. ONLY if NO documents contain ANY relevant information at all, respond with exactly: "No data source found in the 1421 Foundation knowledge base for this query. Please try a different search term or browse the Documents section directly."
6. Write in clear, academic UK English with clear paragraph structure.
7. Be specific and factual — include specific names, dates, and details from the documents."""


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
    # =========================================================================
    # PART 1: KNOWN HISTORICAL VOYAGES (Zheng He's documented expeditions)
    # These destinations are verified by Ming dynasty records and accepted by scholars.
    # =========================================================================
    {"name": "Nanjing", "lat": 32.06, "lon": 118.80, "year": 1403, "event": "Treasure fleet built/commissioned in Nanjing shipyards", "evidence": "Imperial Ming records [citation:1]"},
    {"name": "Nanjing", "lat": 32.06, "lon": 118.80, "year": 1405, "event": "First voyage departs from China", "evidence": "Official Ming dynasty histories [citation:1]"},
    {"name": "Calicut", "lat": 11.26, "lon": 75.78, "year": 1407, "event": "Voyage 1 — Calicut (Malabar Coast, India). Primary destination for trade.", "evidence": "Ma Huan's Ying-Yai Sheng-Lan (The Overall Survey of the Ocean's Shores) [citation:3]"},
    {"name": "Malacca", "lat": 2.19, "lon": 102.25, "year": 1406, "event": "Voyage 1 — Malacca strategic port established", "evidence": "Ming dynasty records and Malacca's historical chronicles [citation:3]"},
    {"name": "Siam", "lat": 13.74, "lon": 100.52, "year": 1408, "event": "Voyage 2 — diplomatic relations with Siam", "evidence": "Ming Shilu (Veritable Records of the Ming) [citation:3]"},
    {"name": "Sri Lanka", "lat": 7.87, "lon": 80.77, "year": 1409, "event": "Voyage 2 — Galle (Sri Lanka) trading contact", "evidence": "Trilingual inscription at Galle (Chinese, Tamil, Persian) [citation:3]"},
    {"name": "Hormuz", "lat": 27.16, "lon": 56.28, "year": 1414, "event": "Voyage 4 — Persian Gulf reached", "evidence": "Ma Huan's accounts; Ming court records [citation:3]"},
    {"name": "Aden", "lat": 12.79, "lon": 45.02, "year": 1417, "event": "Voyage 5 — Arabian Peninsula reached", "evidence": "Ming court records of tribute missions [citation:3]"},
    {"name": "Mogadishu", "lat": 2.05, "lon": 45.32, "year": 1418, "event": "Voyage 5 — Somali Coast trading contact", "evidence": "Ma Huan's Ying-Yai Sheng-Lan [citation:3]"},
    {"name": "Malindi", "lat": -3.22, "lon": 40.12, "year": 1418, "event": "Voyage 5 — Kenya coast embassy exchange", "evidence": "Ma Huan's Ying-Yai Sheng-Lan [citation:3]"},

    # =========================================================================
    # PART 2: HYPOTHESIZED LOCATIONS (Per Gavin Menzies's "1421")
    # IMPORTANT: Professional historians, including Robert Finlay of the Journal of World History,
    # have stated that Menzies's claims are "uniformly without substance" and that his work
    # "flouts the basic rules of both historical study and elementary logic" [citation:3][citation:5].
    # =========================================================================
    {"name": "Australia (West Coast)", "lat": -25.27, "lon": 133.77, "year": 1421, "event": "Menzies: Hong Bao's fleet charted Western Australia; Zhou Man's fleet sailed the Great Barrier Reef [citation:1][citation:9]", "evidence": "Menzies cites: 1) Professor Zhiqiang Zhang's interpretation of the Wu Pei Chih chart; 2) European Dieppe maps showing 'Java La Grande'; 3) alleged shipwrecks; 4) stone inscriptions at Mundaring [citation:9]"},
    {"name": "New Zealand", "lat": -40.90, "lon": 174.88, "year": 1421, "event": "Menzies: Zhou Man's fleet wrecked on South Island after a tsunami", "evidence": "Menzies cites: 1) 'Carbonized remains of a junk' at Moeraki; 2) The 'Tamil Bell'; 3) Amateur researcher Cedric Bell's claims of a 'Chinese fort' in Christchurch (dismissed by New Zealand archaeologists) [citation:2][citation:9]"},
    {"name": "Newport Tower (Rhode Island)", "lat": 41.49, "lon": -71.31, "year": 1421, "event": "Menzies: Chinese astronomical observatory", "evidence": "Menzies claims this medieval stone tower was built by Chinese explorers. Mainstream historians attribute it to Governor Benedict Arnold in the 17th century [citation:4][citation:5]"},
    {"name": "Bimini Road (Bahamas)", "lat": 25.75, "lon": -79.30, "year": 1421, "event": "Menzies: Chinese ballast stones / breakwater", "evidence": "Menzies claims this underwater rock formation is evidence of Chinese construction. Geologists consider it a natural beachrock formation [citation:4]"},
    {"name": "Sacramento River (California)", "lat": 38.58, "lon": -121.49, "year": 1421, "event": "Menzies: A 200-foot Chinese junk is buried in Glenn County mud", "evidence": "Menzies cites: 1) alleged 'medieval Chinese armor' found in 1936 (now lost); 2) amateur magnetometer readings; 3) shards from well-boring. Archaeologists call the claims 'absurd' and note no verifiable evidence exists [citation:6]"},
    {"name": "British Columbia", "lat": 49.28, "lon": -123.12, "year": 1421, "event": "Menzies: Chinese settlement in Pacific Northwest", "evidence": "Menzies relies on supposed linguistic links between Mandarin and Native Haida language (Haida Gwaii). Linguists and historians reject these claims [citation:1][citation:9]"},
    {"name": "Mexico (Palenque)", "lat": 17.48, "lon": -92.05, "year": 1421, "event": "Menzies: Chinese visited Mayan temples", "evidence": "Menzies claims Chinese influenced Mayan art. Scholars like Robert Finlay call this baseless speculation [citation:3][citation:5]"},
    {"name": "Antarctica", "lat": -82.86, "lon": 135.00, "year": 1421, "event": "Menzies: Hong Bao's fleet explored Antarctic waters", "evidence": "Menzies reinterprets the Piri Reis map (1513) as showing Antarctica based on Chinese charts. Cartographic historians disagree [citation:3][citation:8]"}
]

# ── Document store ────────────────────────────────────────────────────

_docs_store: List[dict] = []
_vector_index = None
_embeddings_model = None

def _clean_text(text: str) -> str:
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

def _deduplicate_docs(docs: List[dict]) -> List[dict]:
    seen_titles: set = set()
    unique = []
    for d in docs:
        t = d.get("title", "").strip().lower()
        t_norm = re.sub(r"^\d+\s+", "", t).strip()
        key = t_norm or t
        if key and key not in seen_titles:
            seen_titles.add(key)
            unique.append(d)
    return unique

def _expand_query(query: str) -> List[str]:
    """Generate search variants for a query to improve recall."""
    expansions = [query]
    q = query.lower()

    # Strip common question openers to get the core topic
    core = re.sub(
        r"^(describe|explain|tell me about|what is|what are|how did|how do|"
        r"why did|why do|summarise|summarize|give me information on|"
        r"provide details on|what does the research say about)\s+",
        "", q
    ).strip()
    if core and core != q:
        expansions.append(core)

    # Topic-specific synonym expansions
    expansions_map = {
        "naval technology":    ["shipbuilding", "ship construction", "vessel design", "treasure ship", "bao chuan", "junk ship", "ming fleet", "warship"],
        "ming dynasty":        ["ming", "ming china", "ming period", "ming court", "yongle"],
        "naval":               ["navy", "maritime", "fleet", "armada", "sea power"],
        "technology":          ["technique", "innovation", "engineering", "design", "method"],
        "ship":                ["vessel", "junk", "treasure ship", "bao chuan", "boat"],
        "navigation":          ["compass", "star chart", "celestial navigation", "dead reckoning", "chart"],
        "construction":        ["shipyard", "timber", "dry dock", "building techniques"],
        "zheng he":            ["zheng he", "cheng ho", "admiral", "treasure fleet commander"],
        "calicut":             ["calicut", "kozhikode", "malabar"],
        "africa":              ["east africa", "mombasa", "malindi", "zanzibar", "mogadishu"],
        "americas":            ["america", "new world", "pre-columbian", "chinese in america"],
        "1421":                ["1421 hypothesis", "gavin menzies", "1421 foundation"],
        "1418 map":            ["1418 map", "zheng he map", "liu gang map", "chinese world map"],
        "evidence":            ["evidence", "proof", "artefact", "ceramic", "archaeology"],
        "genetics":            ["dna", "genetic", "ancestry", "haplogroup"],
        "australia":           ["australia", "australian", "aboriginal", "broome", "darwin"],
        "new zealand":         ["new zealand", "maori", "waitaha", "nz"],
    }

    for topic, synonyms in expansions_map.items():
        if topic in q:
            expansions.extend(synonyms)
        else:
            for word in topic.split():
                if word in q and len(word) > 3:
                    expansions.extend(synonyms)
                    break

    # Add individual important words as standalone searches
    stop_words = {"describe", "explain", "what", "how", "did", "the", "and", "for", "tell", "about", "give", "me", "does", "say"}
    important_words = [w for w in core.split() if len(w) > 4 and w not in stop_words]
    expansions.extend(important_words[:5])

    return list(dict.fromkeys(expansions))  # deduplicate while preserving order


def get_relevant_context(query: str, top_k: int = 10) -> tuple:
    """Retrieve relevant documents using multi-strategy search with query expansion."""
    docs = []
    seen_ids: set = set()

    expanded = _expand_query(query)
    print(f"Query: '{query}' → {len(expanded)} search variants")

    # Strategy 1: Semantic search for each expansion (most important)
    for sq in expanded[:10]:
        for d in search_semantic(sq, top_k):
            if d["id"] not in seen_ids:
                docs.append(d)
                seen_ids.add(d["id"])

    # Strategy 2: Keyword search on original query
    for d in search_keyword(query, top_k * 2):
        if d["id"] not in seen_ids:
            docs.append(d)
            seen_ids.add(d["id"])

    # Strategy 3: Keyword search on each expansion
    for sq in expanded[1:6]:
        for d in search_keyword(sq, top_k):
            if d["id"] not in seen_ids:
                docs.append(d)
                seen_ids.add(d["id"])

    # Strategy 4: Title search for quoted or specific terms
    title_match = re.search(r'["\'](.+?)["\']', query)
    if title_match:
        for d in search_by_title(title_match.group(1)):
            if d["id"] not in seen_ids:
                docs.append(d)
                seen_ids.add(d["id"])

    docs = _deduplicate_docs(docs)

    print(f"Found {len(docs)} unique documents")
    if docs:
        print(f"Top 3: {[d['title'][:60] for d in docs[:3]]}")

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
            context += f"{full[:4000]}\n"
        if doc.get("tags"):
            context += f"Tags: {', '.join(doc['tags'])}\n"
        context += "\n"

    return context, docs[:top_k]


def get_comparative_context(query: str, top_k: int = 12) -> tuple:
    """Specialized retrieval for comparative questions like 'compare X to Y'."""
    docs = []
    seen_ids: set = set()
    q = query.lower()

    # Extract the two subjects being compared
    for sep in [" to ", " with ", " and ", " versus ", " vs "]:
        parts = q.replace("compare", "").split(sep)
        if len(parts) >= 2:
            subj1 = parts[0].strip()
            subj2 = parts[1].strip()
            print(f"Comparative: '{subj1}' vs '{subj2}'")
            for d in search_semantic(subj1, top_k // 2):
                if d["id"] not in seen_ids:
                    docs.append(d)
                    seen_ids.add(d["id"])
            for d in search_semantic(subj2, top_k // 2):
                if d["id"] not in seen_ids:
                    docs.append(d)
                    seen_ids.add(d["id"])
            break

    # Also run full query search
    for d in search_semantic(query, top_k):
        if d["id"] not in seen_ids:
            docs.append(d)
            seen_ids.add(d["id"])
    for d in search_keyword(query, top_k):
        if d["id"] not in seen_ids:
            docs.append(d)
            seen_ids.add(d["id"])

    docs = _deduplicate_docs(docs)

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
            context += f"{full[:3000]}\n"
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
async def get_documents(limit: int = Query(default=10000, le=10000), offset: int = 0):
    if not _docs_store:
        return {"documents": [], "total": 0, "limit": limit, "offset": offset}
    total = len(_docs_store)
    paged = _docs_store[offset: offset + limit]
    safe  = [{k: v for k, v in d.items() if k != "content_full"} for d in paged]
    return {"documents": safe, "total": total, "limit": limit, "offset": offset}

@app.get("/api/documents/search")
async def search_documents_endpoint(q: str, limit: int = 50):
    results = []
    seen: set = set()
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

@app.get("/api/documents/{doc_id}")
async def get_document_by_id(doc_id: str):
    for d in _docs_store:
        if d["id"] == doc_id:
            safe = {k: v for k, v in d.items() if k != "content_full"}
            return safe
    raise HTTPException(status_code=404, detail="Document not found")

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
            "\nINSTRUCTIONS:\n"
            "- Answer ONLY from the documents above.\n"
            "- Cite [Document X] after every claim. Cite multiple if applicable: [Document 1][Document 2].\n"
            "- Synthesize across documents to give a full answer.\n"
            "- Structure with clear paragraphs.\n"
        )
    else:
        s += (
            "NO DOCUMENTS FOUND FOR THIS QUERY.\n\n"
            "Respond with exactly: 'No data source found in the 1421 Foundation knowledge base for this query. "
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
        comparative_keywords = ["compare", "versus", "vs", "difference between", "contrast"]
        if any(kw in last.lower() for kw in comparative_keywords):
            context, sources = get_comparative_context(last, top_k=12)
        else:
            context, sources = get_relevant_context(last, top_k=10)

    try:
        response = llm.invoke(_to_lc(_build_system(context), req.messages))
        clean_sources = [
            {"title": d["title"], "author": d["author"], "year": d["year"], "type": d["type"]}
            for d in sources
        ]
        return ChatResponse(
            content=response.content,
            session_id=req.session_id or datetime.now().isoformat(),
            sources=clean_sources if clean_sources else None,
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
async def debug_rag(q: str = "Ming dynasty naval technology"):
    context, docs = get_relevant_context(q, top_k=10)
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
    except Exception as e:
        print(f"Feedback store error: {e}")
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