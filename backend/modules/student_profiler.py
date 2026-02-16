"""
Student Profiler Module
=======================
Handles student profile management and learning analytics
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database.models import (
    Student, Document, QuizAttempt, Quiz,
    LearningSession, PerformanceMetric, ChatHistory
)


class StudentProfiler:
    """
    Manages student profiles and analyzes learning patterns
    """

    def __init__(self):
        print("✅ Student Profiler initialized!")

    def create_student(
        self,
        db: Session,
        name: str,
        email: str,
        preferred_language: str = "en",
        secondary_language: str = "hi"
    ) -> Student:
        """Create a new student profile"""
        student = Student(
            name=name,
            email=email,
            preferred_language=preferred_language,
            secondary_language=secondary_language,
            preferences={}
        )
        db.add(student)
        db.commit()
        db.refresh(student)
        return student

    def get_student(self, db: Session, student_id: int) -> Optional[Student]:
        """Get student by ID"""
        return db.query(Student).filter(Student.id == student_id).first()

    def get_student_by_email(self, db: Session, email: str) -> Optional[Student]:
        """Get student by email"""
        return db.query(Student).filter(Student.email == email).first()

    def update_student(
        self,
        db: Session,
        student_id: int,
        **kwargs
    ) -> Optional[Student]:
        """Update student profile"""
        student = self.get_student(db, student_id)
        if student:
            for key, value in kwargs.items():
                if hasattr(student, key):
                    setattr(student, key, value)
            student.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(student)
        return student

    def get_learning_statistics(
        self,
        db: Session,
        student_id: int
    ) -> Dict:
        """
        Get comprehensive learning statistics for a student
        """
        student = self.get_student(db, student_id)
        if not student:
            return {}

        # Document statistics
        doc_count = db.query(Document).filter(
            Document.student_id == student_id
        ).count()

        # Quiz statistics
        quiz_attempts = db.query(QuizAttempt).filter(
            QuizAttempt.student_id == student_id
        ).all()

        total_quizzes = len(quiz_attempts)
        avg_score = 0
        if total_quizzes > 0:
            avg_score = sum(a.percentage for a in quiz_attempts) / total_quizzes

        # Learning session statistics
        sessions = db.query(LearningSession).filter(
            LearningSession.student_id == student_id
        ).all()

        total_study_time = sum(s.duration_minutes for s in sessions)

        # Recent activity
        recent_sessions = db.query(LearningSession).filter(
            LearningSession.student_id == student_id,
            LearningSession.started_at >= datetime.utcnow() - timedelta(days=7)
        ).count()

        # Performance trends
        recent_quizzes = db.query(QuizAttempt).filter(
            QuizAttempt.student_id == student_id
        ).order_by(QuizAttempt.started_at.desc()).limit(5).all()

        score_trend = [
            {
                "date": q.started_at.isoformat() if q.started_at else None,
                "score": q.percentage
            }
            for q in recent_quizzes
        ]

        return {
            "student_id": student_id,
            "student_name": student.name,
            "documents_uploaded": doc_count,
            "total_quizzes_taken": total_quizzes,
            "average_quiz_score": round(avg_score, 2),
            "total_study_time_minutes": total_study_time,
            "sessions_this_week": recent_sessions,
            "score_trend": score_trend,
            "preferred_language": student.preferred_language,
            "secondary_language": student.secondary_language,
            "member_since": student.created_at.isoformat() if student.created_at else None
        }

    def get_weak_areas(
        self,
        db: Session,
        student_id: int
    ) -> List[Dict]:
        """
        Identify weak areas based on quiz performance
        """
        # Get all quiz attempts with low scores
        weak_attempts = db.query(QuizAttempt).filter(
            QuizAttempt.student_id == student_id,
            QuizAttempt.percentage < 60
        ).all()

        weak_areas = []
        topic_scores = {}

        for attempt in weak_attempts:
            quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
            if quiz and quiz.topic:
                if quiz.topic not in topic_scores:
                    topic_scores[quiz.topic] = {
                        "scores": [],
                        "subject": quiz.subject
                    }
                topic_scores[quiz.topic]["scores"].append(attempt.percentage)

        for topic, data in topic_scores.items():
            avg_score = sum(data["scores"]) / len(data["scores"])
            weak_areas.append({
                "topic": topic,
                "subject": data["subject"],
                "average_score": round(avg_score, 2),
                "attempts": len(data["scores"]),
                "priority": "high" if avg_score < 40 else "medium"
            })

        # Sort by score (lowest first)
        weak_areas.sort(key=lambda x: x["average_score"])

        return weak_areas

    def get_strong_areas(
        self,
        db: Session,
        student_id: int
    ) -> List[Dict]:
        """
        Identify strong areas based on quiz performance
        """
        strong_attempts = db.query(QuizAttempt).filter(
            QuizAttempt.student_id == student_id,
            QuizAttempt.percentage >= 80
        ).all()

        strong_areas = []
        topic_scores = {}

        for attempt in strong_attempts:
            quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
            if quiz and quiz.topic:
                if quiz.topic not in topic_scores:
                    topic_scores[quiz.topic] = {
                        "scores": [],
                        "subject": quiz.subject
                    }
                topic_scores[quiz.topic]["scores"].append(attempt.percentage)

        for topic, data in topic_scores.items():
            avg_score = sum(data["scores"]) / len(data["scores"])
            strong_areas.append({
                "topic": topic,
                "subject": data["subject"],
                "average_score": round(avg_score, 2),
                "attempts": len(data["scores"]),
                "mastery": "excellent" if avg_score >= 90 else "good"
            })

        strong_areas.sort(key=lambda x: x["average_score"], reverse=True)

        return strong_areas

    def record_learning_session(
        self,
        db: Session,
        student_id: int,
        session_type: str,
        topic: str = None,
        subject: str = None,
        duration_minutes: int = 0,
        queries: List[str] = None
    ) -> LearningSession:
        """Record a learning session"""
        session = LearningSession(
            student_id=student_id,
            session_type=session_type,
            topic=topic,
            subject=subject,
            duration_minutes=duration_minutes,
            queries=queries or [],
            started_at=datetime.utcnow()
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def update_performance_metric(
        self,
        db: Session,
        student_id: int,
        subject: str,
        topic: str,
        score: float
    ):
        """Update or create performance metric"""
        metric = db.query(PerformanceMetric).filter(
            PerformanceMetric.student_id == student_id,
            PerformanceMetric.subject == subject,
            PerformanceMetric.topic == topic
        ).first()

        if metric:
            # Update existing metric
            old_avg = metric.average_score
            old_attempts = metric.total_attempts

            new_attempts = old_attempts + 1
            new_avg = ((old_avg * old_attempts) + score) / new_attempts

            # Calculate improvement
            improvement = score - old_avg

            metric.average_score = new_avg
            metric.total_attempts = new_attempts
            metric.improvement_rate = improvement
            metric.mastery_level = min(100, new_avg * 1.1)  # Slight boost
            metric.last_activity = datetime.utcnow()
            metric.updated_at = datetime.utcnow()
        else:
            # Create new metric
            metric = PerformanceMetric(
                student_id=student_id,
                subject=subject,
                topic=topic,
                average_score=score,
                total_attempts=1,
                improvement_rate=0,
                mastery_level=score,
                last_activity=datetime.utcnow()
            )
            db.add(metric)

        db.commit()

    def get_study_streak(
        self,
        db: Session,
        student_id: int
    ) -> Dict:
        """Calculate study streak (consecutive days)"""
        sessions = db.query(LearningSession).filter(
            LearningSession.student_id == student_id
        ).order_by(LearningSession.started_at.desc()).all()

        if not sessions:
            return {"current_streak": 0, "longest_streak": 0}

        # Calculate current streak
        today = datetime.utcnow().date()
        current_streak = 0
        check_date = today

        session_dates = set(s.started_at.date() for s in sessions if s.started_at)

        while check_date in session_dates or (check_date == today and today not in session_dates):
            if check_date in session_dates:
                current_streak += 1
            check_date -= timedelta(days=1)
            if check_date not in session_dates and check_date != today:
                break

        return {
            "current_streak": current_streak,
            "longest_streak": current_streak,  # Simplified
            "active_today": today in session_dates
        }


# Singleton instance
student_profiler = StudentProfiler()
