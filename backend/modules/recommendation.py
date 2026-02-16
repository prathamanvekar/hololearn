"""
Recommendation System Module
============================
Provides personalized content recommendations
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import numpy as np

from backend.database.models import (
    Student, Document, Quiz, QuizAttempt,
    PerformanceMetric, DocumentChunk
)
from backend.modules.nlp_engine import nlp_engine
from backend.modules.llm_service import llm_service
from backend.modules.student_profiler import student_profiler


class RecommendationEngine:
    """
    Hybrid recommendation system combining:
    - Content-based filtering (using embeddings)
    - Performance-based recommendations
    - LLM-powered suggestions
    """

    def __init__(self):
        print("✅ Recommendation Engine initialized!")

    def get_content_recommendations(
        self,
        db: Session,
        student_id: int,
        num_recommendations: int = 5
    ) -> List[Dict]:
        """
        Get content recommendations based on student's learning history
        """
        # Get student's weak areas
        weak_areas = student_profiler.get_weak_areas(db, student_id)

        # Get all available topics from documents
        documents = db.query(Document).filter(
            Document.student_id == student_id,
            Document.is_processed == True
        ).all()

        available_topics = list(set(
            doc.topic for doc in documents if doc.topic
        ))

        recommendations = []

        # Prioritize weak areas
        for weak in weak_areas[:3]:
            recommendations.append({
                "type": "review",
                "topic": weak["topic"],
                "subject": weak["subject"],
                "reason": f"Your average score is {weak['average_score']}%. Review recommended.",
                "priority": weak["priority"]
            })

        # Find similar topics to explore
        if weak_areas and available_topics:
            weak_topics = [w["topic"] for w in weak_areas]
            for topic in weak_topics[:2]:
                similar = nlp_engine.find_similar_topics(
                    topic,
                    available_topics,
                    top_k=2
                )
                for sim_topic, score in similar:
                    if sim_topic not in weak_topics and score > 0.5:
                        recommendations.append({
                            "type": "explore",
                            "topic": sim_topic,
                            "reason": f"Related to {topic} (similarity: {score:.0%})",
                            "priority": "medium"
                        })

        return recommendations[:num_recommendations]

    def get_quiz_recommendations(
        self,
        db: Session,
        student_id: int
    ) -> List[Dict]:
        """
        Recommend quizzes based on performance
        """
        # Get topics that haven't been quizzed recently
        recent_attempts = db.query(QuizAttempt).filter(
            QuizAttempt.student_id == student_id
        ).order_by(QuizAttempt.started_at.desc()).limit(10).all()

        recent_quiz_ids = [a.quiz_id for a in recent_attempts]

        # Get quizzes not recently attempted
        available_quizzes = db.query(Quiz).filter(
            ~Quiz.id.in_(recent_quiz_ids) if recent_quiz_ids else True
        ).limit(5).all()

        recommendations = []
        for quiz in available_quizzes:
            recommendations.append({
                "quiz_id": quiz.id,
                "title": quiz.title,
                "topic": quiz.topic,
                "difficulty": quiz.difficulty,
                "reason": "Not attempted recently"
            })

        # Add retry recommendations for failed quizzes
        failed_attempts = db.query(QuizAttempt).filter(
            QuizAttempt.student_id == student_id,
            QuizAttempt.percentage < 60
        ).order_by(QuizAttempt.started_at.desc()).limit(3).all()

        for attempt in failed_attempts:
            quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
            if quiz:
                recommendations.append({
                    "quiz_id": quiz.id,
                    "title": quiz.title,
                    "topic": quiz.topic,
                    "difficulty": quiz.difficulty,
                    "reason": f"Previous score: {attempt.percentage:.0f}%. Retry recommended.",
                    "retry": True
                })

        return recommendations

    def get_personalized_study_plan(
        self,
        db: Session,
        student_id: int,
        days: int = 7
    ) -> Dict:
        """
        Generate a personalized study plan
        """
        student = student_profiler.get_student(db, student_id)
        if not student:
            return {}

        stats = student_profiler.get_learning_statistics(db, student_id)
        weak_areas = student_profiler.get_weak_areas(db, student_id)
        strong_areas = student_profiler.get_strong_areas(db, student_id)

        # Get available topics
        documents = db.query(Document).filter(
            Document.student_id == student_id
        ).all()
        available_topics = list(set(doc.topic for doc in documents if doc.topic))

        # Use LLM to generate recommendations
        performance_data = {
            "average_score": stats.get("average_quiz_score", 0),
            "weak_areas": [w["topic"] for w in weak_areas[:3]],
            "strong_areas": [s["topic"] for s in strong_areas[:3]],
            "study_time_this_week": stats.get("total_study_time_minutes", 0)
        }

        recommendations = llm_service.get_recommendations(
            student_performance=performance_data,
            available_topics=available_topics,
            language=student.preferred_language
        )

        # Build study plan
        study_plan = {
            "student_name": student.name,
            "plan_duration_days": days,
            "daily_recommended_minutes": 30,
            "focus_topics": recommendations.get("priority_topics", []),
            "strengths": recommendations.get("strengths", []),
            "areas_to_improve": recommendations.get("areas_to_improve", []),
            "study_tips": recommendations.get("study_tips", []),
            "next_steps": recommendations.get("recommended_next_steps", []),
            "generated_at": None
        }

        from datetime import datetime
        study_plan["generated_at"] = datetime.utcnow().isoformat()

        return study_plan

    def get_similar_documents(
        self,
        db: Session,
        document_id: int,
        student_id: int,
        top_k: int = 3
    ) -> List[Dict]:
        """
        Find similar documents based on content
        """
        # Get the source document
        source_doc = db.query(Document).filter(
            Document.id == document_id
        ).first()

        if not source_doc:
            return []

        # Get all other documents
        other_docs = db.query(Document).filter(
            Document.student_id == student_id,
            Document.id != document_id,
            Document.is_processed == True
        ).all()

        if not other_docs:
            return []

        # Get embeddings for comparison
        # Use document topics/titles for similarity
        source_text = f"{source_doc.title or ''} {source_doc.topic or ''} {source_doc.subject or ''}"
        other_texts = [
            f"{doc.title or ''} {doc.topic or ''} {doc.subject or ''}"
            for doc in other_docs
        ]

        source_embedding = nlp_engine.get_single_embedding(source_text)
        other_embeddings = nlp_engine.get_embeddings(other_texts)

        similarities = nlp_engine.compute_similarity(source_embedding, other_embeddings)

        # Get top-k similar
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        similar_docs = []
        for idx in top_indices:
            if similarities[idx] > 0.3:  # Threshold
                doc = other_docs[idx]
                similar_docs.append({
                    "document_id": doc.id,
                    "filename": doc.filename,
                    "title": doc.title,
                    "topic": doc.topic,
                    "similarity": float(similarities[idx])
                })

        return similar_docs


# Singleton instance
recommendation_engine = RecommendationEngine()
