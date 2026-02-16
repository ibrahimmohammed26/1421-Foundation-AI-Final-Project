from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    mode: str = "auto"

class ChatResponse(BaseModel):
    session_id: str
    question: str
    answer: str
    sources_used: List[str]
    document_results: List[Dict]
    web_results: List[Dict]
    total_results: int

class SessionResponse(BaseModel):
    session_id: str
    name: str
    created_at: datetime

class NewSessionRequest(BaseModel):
    name: Optional[str] = None

class DocumentResponse(BaseModel):
    id: int
    title: str
    author: str
    source_type: str
    word_count: int

class LocationResponse(BaseModel):
    name: str
    lat: float
    lon: float
    year: int
    event: str