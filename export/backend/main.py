"""
1421 Foundation Research System — FastAPI Backend
Stack: FastAPI + LangChain + PostgreSQL/PostGIS
"""

import os
from datetime import datetime
from typing import Optional

# FastAPI
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Pydantic
from pydantic import BaseModel

# LangChain OpenAI
from langchain_openai import ChatOpenAI

# LangChain Core Messages
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate

# PostgreSQL
import psycopg2
from psycopg2.extras import RealDictCursor

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


from fastapi.responses import StreamingResponse


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
        return {"feedback_count": feedback_count, "locations_count": len(VOYAGE_LOCATIONS)}
    except Exception:
        return {"feedback_count": 0, "locations_count": len(VOYAGE_LOCATIONS)}


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
    except Exception as e:
        print(f"DB init skipped: {e}")
