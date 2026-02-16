"""
Profile Routes
==============
Handles student profile management
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from backend.database.connection import get_db
from backend.database.models import Student
from backend.modules.student_profiler import student_profiler
from backend.modules.recommendation import recommendation_engine

router = APIRouter(prefix="/profile", tags=["Profile"])


class CreateStudentRequest(BaseModel):
    name: str
    email: str
    preferred_language: Optional[str] = "en"
    secondary_language: Optional[str] = "hi"


class UpdateStudentRequest(BaseModel):
    name: Optional[str] = None
    preferred_language: Optional[str] = None
    secondary_language: Optional[str] = None
    preferences: Optional[dict] = None


@router.post("/create")
async def create_student(request: CreateStudentRequest, db: Session = Depends(get_db)):
    """
    Create a new student profile
    """
    # Check if email exists
    existing = student_profiler.get_student_by_email(db, request.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    student = student_profiler.create_student(
        db=db,
        name=request.name,
        email=request.email,
        preferred_language=request.preferred_language,
        secondary_language=request.secondary_language
    )

    return {
        "success": True,
        "student_id": student.id,
        "message": "Student profile created successfully"
    }


@router.get("/{student_id}")
async def get_student_profile(student_id: int, db: Session = Depends(get_db)):
    """
    Get student profile
    """
    student = student_profiler.get_student(db, student_id)

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    return {
        "id": student.id,
        "name": student.name,
        "email": student.email,
        "preferred_language": student.preferred_language,
        "secondary_language": student.secondary_language,
        "preferences": student.preferences,
        "created_at": student.created_at.isoformat() if student.created_at else None
    }


@router.put("/{student_id}")
async def update_student_profile(
    student_id: int,
    request: UpdateStudentRequest,
    db: Session = Depends(get_db)
):
    """
    Update student profile
    """
    update_data = {k: v for k, v in request.dict().items() if v is not None}

    student = student_profiler.update_student(db, student_id, **update_data)

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    return {
        "success": True,
        "message": "Profile updated successfully"
    }


@router.get("/{student_id}/statistics")
async def get_student_statistics(student_id: int, db: Session = Depends(get_db)):
    """
    Get comprehensive learning statistics
    """
    stats = student_profiler.get_learning_statistics(db, student_id)

    if not stats:
        raise HTTPException(status_code=404, detail="Student not found")

    return stats


@router.get("/{student_id}/weak-areas")
async def get_weak_areas(student_id: int, db: Session = Depends(get_db)):
    """
    Get student's weak areas
    """
    weak_areas = student_profiler.get_weak_areas(db, student_id)
    return {"weak_areas": weak_areas}


@router.get("/{student_id}/strong-areas")
async def get_strong_areas(student_id: int, db: Session = Depends(get_db)):
    """
    Get student's strong areas
    """
    strong_areas = student_profiler.get_strong_areas(db, student_id)
    return {"strong_areas": strong_areas}


@router.get("/{student_id}/recommendations")
async def get_recommendations(student_id: int, db: Session = Depends(get_db)):
    """
    Get personalized content recommendations
    """
    recommendations = recommendation_engine.get_content_recommendations(
        db=db,
        student_id=student_id
    )

    return {"recommendations": recommendations}


@router.get("/{student_id}/study-plan")
async def get_study_plan(
    student_id: int,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """
    Get personalized study plan
    """
    study_plan = recommendation_engine.get_personalized_study_plan(
        db=db,
        student_id=student_id,
        days=days
    )

    return study_plan


@router.get("/{student_id}/streak")
async def get_study_streak(student_id: int, db: Session = Depends(get_db)):
    """
    Get study streak information
    """
    streak = student_profiler.get_study_streak(db, student_id)
    return streak
