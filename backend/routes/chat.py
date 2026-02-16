"""
Chat Routes
===========
Handles chat and conversation endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from backend.database.connection import get_db
from backend.database.models import ChatHistory, Student
from backend.modules.rag_engine import rag_engine
from backend.modules.llm_service import llm_service
from backend.modules.nlp_engine import nlp_engine
from backend.modules.translator import translator

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    student_id: int
    message: str
    session_id: Optional[str] = None
    language: Optional[str] = "en"
    bilingual: Optional[bool] = False


class ChatResponse(BaseModel):
    response: str
    response_secondary: Optional[str] = None
    intent: str
    sources: List[dict] = []
    language: str
    session_id: str


@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Send a message and get AI response
    """
    requested_language = (request.language or "en").lower()
    if requested_language not in {"en", "hi"}:
        requested_language = "en"

    # Generate session ID if not provided
    session_id = request.session_id or f"session_{request.student_id}_{datetime.utcnow().timestamp()}"

    # Detect intent
    intent_result = nlp_engine.classify_intent_with_bert(request.message)
    intent = intent_result["intent"]

    # Detect language of input
    detected_lang = nlp_engine.detect_language_with_bert(request.message)

    # Get student info
    student = db.query(Student).filter(Student.id == request.student_id).first()
    student_name = student.name if student else "Student"

    # Get relevant context from RAG
    context, source_chunks = rag_engine.get_context_for_query(
        query=request.message,
        student_id=request.student_id,
        max_tokens=2000,
        top_k=5
    )

    # Get chat history for context
    history = db.query(ChatHistory).filter(
        ChatHistory.student_id == request.student_id,
        ChatHistory.session_id == session_id
    ).order_by(ChatHistory.created_at.desc()).limit(6).all()

    chat_history = [
        {"role": h.role, "content": h.content}
        for h in reversed(history)
    ]

    # Generate response
    if request.bilingual:
        # Bilingual mode (current scope): show the selected language first,
        # then provide the other language under translation.
        primary_lang = requested_language
        secondary_lang = "hi" if primary_lang == "en" else "en"

        responses = llm_service.generate_bilingual_response(
            query=request.message,
            context=context,
            primary_lang=primary_lang,
            secondary_lang=secondary_lang,
        )
        response_text = responses.get(primary_lang, "")
        response_secondary = responses.get(secondary_lang, "")
        response_language = primary_lang
    else:
        # Generate single language response
        response_text = llm_service.chat_with_context(
            query=request.message,
            context=context,
            chat_history=chat_history,
            language=requested_language,
            student_name=student_name
        )
        response_secondary = None
        response_language = requested_language

    # Save to chat history
    # Save user message
    user_msg = ChatHistory(
        student_id=request.student_id,
        session_id=session_id,
        role="user",
        content=request.message,
        language=detected_lang["language"] if isinstance(detected_lang, dict) else detected_lang,
        intent=intent
    )
    db.add(user_msg)

    # Save assistant message
    assistant_msg = ChatHistory(
        student_id=request.student_id,
        session_id=session_id,
        role="assistant",
        content=response_text,
        language=response_language,
        referenced_documents=[c["metadata"].get("document_id") for c in source_chunks]
    )
    db.add(assistant_msg)
    db.commit()

    # Format sources
    sources = [
        {
            "chunk_id": chunk["chunk_id"],
            "relevance": round(chunk["relevance_score"], 2),
            "preview": chunk["content"][:200] + "..."
        }
        for chunk in source_chunks[:3]
    ]

    return ChatResponse(
        response=response_text,
        response_secondary=response_secondary,
        intent=intent,
        sources=sources,
        language=response_language,
        session_id=session_id
    )


class ExplainRequest(BaseModel):
    student_id: int
    concept: str
    language: Optional[str] = "en"
    level: Optional[str] = "intermediate"


@router.post("/explain")
async def explain_concept(request: ExplainRequest, db: Session = Depends(get_db)):
    """
    Get detailed explanation of a concept
    """
    # Get relevant context
    context, _ = rag_engine.get_context_for_query(
        query=request.concept,
        student_id=request.student_id,
        max_tokens=1500
    )

    explanation = llm_service.explain_concept(
        concept=request.concept,
        context=context,
        language=request.language,
        level=request.level
    )

    return {
        "concept": request.concept,
        "explanation": explanation,
        "language": request.language,
        "level": request.level
    }


class SummarizeRequest(BaseModel):
    student_id: int
    document_id: Optional[int] = None
    text: Optional[str] = None
    language: Optional[str] = "en"


@router.post("/summarize")
async def summarize_content(request: SummarizeRequest, db: Session = Depends(get_db)):
    """
    Generate summary of content or document
    """
    if request.document_id:
        # Get document content from RAG
        content, _ = rag_engine.get_context_for_query(
            query="main topics and key concepts",
            student_id=request.student_id,
            max_tokens=3000
        )
    elif request.text:
        content = request.text
    else:
        raise HTTPException(status_code=400, detail="Provide document_id or text")

    summary = llm_service.generate_summary(
        content=content,
        language=request.language
    )

    return {
        "summary": summary,
        "language": request.language
    }


@router.get("/history/{student_id}")
async def get_chat_history(
    student_id: int,
    session_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get chat history for a student
    """
    query = db.query(ChatHistory).filter(ChatHistory.student_id == student_id)

    if session_id:
        query = query.filter(ChatHistory.session_id == session_id)

    history = query.order_by(ChatHistory.created_at.desc()).limit(limit).all()

    return {
        "history": [
            {
                "id": h.id,
                "role": h.role,
                "content": h.content,
                "language": h.language,
                "intent": h.intent,
                "timestamp": h.created_at.isoformat() if h.created_at else None
            }
            for h in reversed(history)
        ]
    }


@router.post("/translate")
async def translate_text(
    text: str,
    source_lang: str = "en",
    target_lang: str = "hi"
):
    """
    Translate text between languages
    """
    translated = translator.translate(text, source_lang, target_lang)
    return {
        "original": text,
        "translated": translated,
        "source_language": source_lang,
        "target_language": target_lang
    }
