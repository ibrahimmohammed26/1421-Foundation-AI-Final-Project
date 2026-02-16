from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500))
    author = Column(String(200))
    content = Column(Text)
    source_type = Column(String(50))  # pdf, email, scanned
    file_path = Column(String(500))
    metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    word_count = Column(Integer, default=0)

class Location(Base):
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200))
    description = Column(Text)
    year = Column(Integer)
    event = Column(String(500))
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True)
    name = Column(String(200))
    history = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class SearchAnalytics(Base):
    __tablename__ = "search_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String(500))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    response_time = Column(Float)
    sources_used = Column(JSON)
    result_count = Column(Integer)