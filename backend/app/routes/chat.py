from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.database import get_db
from app.services.llm_service import LLMService
from app import schemas, models

router = APIRouter()
llm_service = LLMService()

@router.post("/ask", response_model=schemas.ChatResponse)
async def ask_question(
    request: schemas.ChatRequest,
    db: Session = Depends(get_db)
):
    """Ask a question and get AI-generated answer"""
    
    # Generate answer using your vector DB and OpenAI
    result = await llm_service.generate_answer(
        question=request.question,
        mode=request.mode,
        session_id=request.session_id
    )
    
    # Create or update session
    session_id = request.session_id
    if not session_id:
        session_id = str(uuid.uuid4())
        
        # Create new session
        new_session = models.ChatSession(
            session_id=session_id,
            name=request.question[:50] + "...",
            history=[]
        )
        db.add(new_session)
        db.commit()
    
    # Save to chat history
    chat_session = db.query(models.ChatSession).filter(
        models.ChatSession.session_id == session_id
    ).first()
    
    if chat_session:
        history = chat_session.history or []
        history.append({
            "question": request.question,
            "answer": result["answer"],
            "timestamp": datetime.now().isoformat(),
            "sources_used": result["sources_used"]
        })
        chat_session.history = history
        chat_session.updated_at = datetime.now()
        db.commit()
    
    return schemas.ChatResponse(
        session_id=session_id,
        question=request.question,
        answer=result["answer"],
        sources_used=result["sources_used"],
        document_results=result["document_results"],
        web_results=result["web_results"],
        total_results=result["total_results"]
    )

@router.get("/sessions", response_model=List[schemas.SessionResponse])
async def get_sessions(
    db: Session = Depends(get_db),
    limit: int = 20
):
    """Get recent chat sessions"""
    
    sessions = db.query(models.ChatSession).order_by(
        models.ChatSession.updated_at.desc()
    ).limit(limit).all()
    
    return [
        schemas.SessionResponse(
            session_id=s.session_id,
            name=s.name,
            created_at=s.created_at
        ) for s in sessions
    ]

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Delete a chat session"""
    
    db.query(models.ChatSession).filter(
        models.ChatSession.session_id == session_id
    ).delete()
    db.commit()
    
    return {"message": "Session deleted"}