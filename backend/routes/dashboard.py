"""
Dashboard Routes
================
Handles dashboard and analytics endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional

from backend.database.connection import get_db
from backend.database.models import (
    Student, Document, Quiz, QuizAttempt,
    LearningSession, PerformanceMetric
)
from backend.modules.student_profiler import student_profiler
from backend.modules.recommendation import recommendation_engine

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/{student_id}")
async def get_dashboard(student_id: int, db: Session = Depends(get_db)):
    """
    Get complete dashboard data for a student
    """
    student = student_profiler.get_student(db, student_id)

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Get statistics
    stats = student_profiler.get_learning_statistics(db, student_id)

    # Get weak and strong areas
    weak_areas = student_profiler.get_weak_areas(db, student_id)
    strong_areas = student_profiler.get_strong_areas(db, student_id)

    # Get study streak
    streak = student_profiler.get_study_streak(db, student_id)

    # Get recent activity
    recent_sessions = db.query(LearningSession).filter(
        LearningSession.student_id == student_id
    ).order_by(LearningSession.started_at.desc()).limit(5).all()

    recent_activity = [
        {
            "type": s.session_type,
            "topic": s.topic,
            "duration": s.duration_minutes,
            "date": s.started_at.isoformat() if s.started_at else None
        }
        for s in recent_sessions
    ]

    # Get recommendations
    recommendations = recommendation_engine.get_content_recommendations(
        db=db,
        student_id=student_id,
        num_recommendations=3
    )

    return {
        "student": {
            "id": student.id,
            "name": student.name,
            "email": student.email
        },
        "statistics": stats,
        "streak": streak,
        "weak_areas": weak_areas[:3],
        "strong_areas": strong_areas[:3],
        "recent_activity": recent_activity,
        "recommendations": recommendations
    }


@router.get("/{student_id}/performance-chart")
async def get_performance_chart_data(
    student_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get performance data for charting
    """
    start_date = datetime.utcnow() - timedelta(days=days)

    # Get quiz attempts in date range
    attempts = db.query(QuizAttempt).filter(
        QuizAttempt.student_id == student_id,
        QuizAttempt.started_at >= start_date
    ).order_by(QuizAttempt.started_at).all()

    # Format for chart
    chart_data = [
        {
            "date": a.started_at.strftime("%Y-%m-%d") if a.started_at else None,
            "score": a.percentage,
            "quiz_id": a.quiz_id
        }
        for a in attempts
    ]

    # Calculate average by date
    date_scores = {}
    for item in chart_data:
        if item["date"]:
            if item["date"] not in date_scores:
                date_scores[item["date"]] = []
            date_scores[item["date"]].append(item["score"])

    daily_averages = [
        {
            "date": date,
            "average_score": sum(scores) / len(scores)
        }
        for date, scores in sorted(date_scores.items())
    ]

    return {
        "raw_data": chart_data,
        "daily_averages": daily_averages,
        "period_days": days
    }


@router.get("/{student_id}/subject-breakdown")
async def get_subject_breakdown(student_id: int, db: Session = Depends(get_db)):
    """
    Get performance breakdown by subject
    """
    metrics = db.query(PerformanceMetric).filter(
        PerformanceMetric.student_id == student_id
    ).all()

    # Group by subject
    subject_data = {}
    for metric in metrics:
        if metric.subject not in subject_data:
            subject_data[metric.subject] = {
                "topics": [],
                "total_score": 0,
                "count": 0
            }

        subject_data[metric.subject]["topics"].append({
            "topic": metric.topic,
            "average_score": metric.average_score,
            "mastery_level": metric.mastery_level,
            "attempts": metric.total_attempts
        })
        subject_data[metric.subject]["total_score"] += metric.average_score
        subject_data[metric.subject]["count"] += 1

    # Calculate subject averages
    breakdown = []
    for subject, data in subject_data.items():
        avg = data["total_score"] / data["count"] if data["count"] > 0 else 0
        breakdown.append({
            "subject": subject,
            "average_score": round(avg, 2),
            "topics": data["topics"],
            "total_topics": len(data["topics"])
        })

    return {"subjects": breakdown}


@router.get("/{student_id}/activity-heatmap")
async def get_activity_heatmap(
    student_id: int,
    weeks: int = 12,
    db: Session = Depends(get_db)
):
    """
    Get activity data for heatmap visualization
    """
    start_date = datetime.utcnow() - timedelta(weeks=weeks)

    sessions = db.query(LearningSession).filter(
        LearningSession.student_id == student_id,
        LearningSession.started_at >= start_date
    ).all()

    # Count sessions per day
    activity = {}
    for session in sessions:
        if session.started_at:
            date_str = session.started_at.strftime("%Y-%m-%d")
            activity[date_str] = activity.get(date_str, 0) + 1

    return {
        "activity": activity,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": datetime.utcnow().strftime("%Y-%m-%d")
    }
