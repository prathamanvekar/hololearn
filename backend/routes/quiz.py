"""
Quiz Routes
===========
Handles quiz generation and grading
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, List

from backend.database.connection import get_db
from backend.database.models import Quiz
from backend.modules.quiz_generator import quiz_generator

router = APIRouter(prefix="/quiz", tags=["Quiz"])


class GenerateQuizRequest(BaseModel):
    student_id: int
    document_id: Optional[int] = None
    topic: Optional[str] = None
    subject: Optional[str] = None
    num_questions: Optional[int] = 1
    difficulty: Optional[str] = "medium"
    language: Optional[str] = "en"


class SubmitQuizRequest(BaseModel):
    student_id: int
    quiz_id: int
    responses: Dict[str, str]  # question_id -> answer
    time_taken_seconds: Optional[int] = 0


@router.post("/generate")
async def generate_quiz(request: GenerateQuizRequest, db: Session = Depends(get_db)):
    """
    Generate a new quiz
    """
    # Token-saver: clamp to a single question for now.
    request.num_questions = 1

    if request.document_id:
        # Generate from document
        quiz = quiz_generator.generate_quiz_from_document(
            db=db,
            document_id=request.document_id,
            num_questions=request.num_questions,
            difficulty=request.difficulty,
            language=request.language
        )
    elif request.topic:
        # Generate from topic
        quiz = quiz_generator.generate_quiz_from_topic(
            db=db,
            student_id=request.student_id,
            topic=request.topic,
            subject=request.subject,
            num_questions=request.num_questions,
            difficulty=request.difficulty,
            language=request.language
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either document_id or topic"
        )

    if not quiz:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate quiz"
        )

    # Get quiz with questions
    quiz_data = quiz_generator.get_quiz(db, quiz.id)

    return {
        "success": True,
        "quiz": quiz_data
    }


@router.get("/{quiz_id}")
async def get_quiz(quiz_id: int, db: Session = Depends(get_db)):
    """
    Get quiz details with questions
    """
    quiz_data = quiz_generator.get_quiz(db, quiz_id)

    if not quiz_data:
        raise HTTPException(status_code=404, detail="Quiz not found")

    return quiz_data


@router.post("/submit")
async def submit_quiz(request: SubmitQuizRequest, db: Session = Depends(get_db)):
    """
    Submit quiz answers and get results
    """
    results = quiz_generator.submit_quiz(
        db=db,
        student_id=request.student_id,
        quiz_id=request.quiz_id,
        responses=request.responses,
        time_taken_seconds=request.time_taken_seconds
    )

    if "error" in results:
        raise HTTPException(status_code=400, detail=results["error"])

    return results


@router.get("/history/{student_id}")
async def get_quiz_history(
    student_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get quiz history for a student
    """
    history = quiz_generator.get_student_quiz_history(
        db=db,
        student_id=student_id,
        limit=limit
    )

    return {"history": history}


@router.get("/list")
async def list_quizzes(
    student_id: Optional[int] = None,
    subject: Optional[str] = None,
    topic: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List available quizzes
    """
    query = db.query(Quiz)

    if subject:
        query = query.filter(Quiz.subject == subject)
    if topic:
        query = query.filter(Quiz.topic == topic)

    quizzes = query.order_by(Quiz.created_at.desc()).limit(20).all()

    return {
        "quizzes": [
            {
                "id": q.id,
                "title": q.title,
                "subject": q.subject,
                "topic": q.topic,
                "difficulty": q.difficulty,
                "language": q.language,
                "created_at": q.created_at.isoformat() if q.created_at else None
            }
            for q in quizzes
        ]
    }
