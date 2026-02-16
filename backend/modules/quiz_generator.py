"""
Quiz Generator Module
=====================
Generates and grades quizzes based on document content
"""

from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from backend.database.models import (
    Quiz, QuizQuestion, QuizAttempt, Document
)
from backend.modules.llm_service import llm_service
from backend.modules.rag_engine import rag_engine
from backend.modules.student_profiler import student_profiler
from backend.config import QUIZ_QUESTIONS_PER_SESSION


class QuizGenerator:
    """
    Generates quizzes from document content using LLM
    """

    def __init__(self):
        print("✅ Quiz Generator initialized!")

    def generate_quiz_from_document(
        self,
        db: Session,
        document_id: int,
        num_questions: int = QUIZ_QUESTIONS_PER_SESSION,
        difficulty: str = "medium",
        language: str = "en"
    ) -> Optional[Quiz]:
        """
        Generate a quiz from a document's content
        """
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return None

        # Get document content from RAG
        stats = rag_engine.get_document_stats()

        # Search for content
        content_chunks = rag_engine.search_documents(
            query=f"{document.topic or document.title or 'main concepts'}",
            document_ids=[document_id],
            top_k=4
        )

        if not content_chunks:
            return None

        # Combine content
        content = "\n\n".join([chunk["content"] for chunk in content_chunks])

        # Keep prompts small to avoid LLM token limits.
        content = content[:8000]

        # Generate questions using LLM
        recent_questions = [
            q[0]
            for q in db.query(QuizQuestion.question_text)
            .join(Quiz, QuizQuestion.quiz_id == Quiz.id)
            .filter(Quiz.document_id == document_id)
            .order_by(QuizQuestion.id.desc())
            .limit(6)
            .all()
        ]

        questions_data = llm_service.generate_quiz(
            content=content,
            num_questions=num_questions,
            difficulty=difficulty,
            language=language,
            avoid_questions=recent_questions,
            nonce=datetime.utcnow().isoformat()
        )

        if not questions_data:
            return None

        # Create quiz in database
        quiz = Quiz(
            title=f"Quiz: {document.title or document.filename}",
            subject=document.subject,
            topic=document.topic,
            difficulty=difficulty,
            language=language,
            document_id=document_id
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)

        # Add questions (hard-limit to requested count)
        for i, q_data in enumerate((questions_data or [])[: max(1, int(num_questions or 1))]):
            question = QuizQuestion(
                quiz_id=quiz.id,
                question_text=q_data.get("question", ""),
                question_type="mcq",
                options=q_data.get("options", []),
                correct_answer=q_data.get("correct_answer", ""),
                explanation=q_data.get("explanation", ""),
                difficulty=difficulty,
                points=1
            )
            db.add(question)

        db.commit()
        db.refresh(quiz)

        return quiz

    def generate_quiz_from_topic(
        self,
        db: Session,
        student_id: int,
        topic: str,
        subject: str = None,
        num_questions: int = QUIZ_QUESTIONS_PER_SESSION,
        difficulty: str = "medium",
        language: str = "en"
    ) -> Optional[Quiz]:
        """
        Generate a quiz on a specific topic using RAG
        """
        # Get relevant content from student's documents
        context, chunks = rag_engine.get_context_for_query(
            query=topic,
            student_id=student_id,
            max_tokens=1200,
            top_k=4
        )

        if not context:
            # Use general knowledge if no documents
            context = f"Topic: {topic}"

        # Keep prompts small to avoid LLM token limits.
        context = context[:8000]

        # Generate questions
        recent_questions = [
            q[0]
            for q in db.query(QuizQuestion.question_text)
            .join(Quiz, QuizQuestion.quiz_id == Quiz.id)
            .filter(Quiz.topic == topic)
            .order_by(QuizQuestion.id.desc())
            .limit(6)
            .all()
        ]

        questions_data = llm_service.generate_quiz(
            content=context,
            num_questions=num_questions,
            difficulty=difficulty,
            language=language,
            avoid_questions=recent_questions,
            nonce=datetime.utcnow().isoformat()
        )

        if not questions_data:
            return None

        # Create quiz
        quiz = Quiz(
            title=f"Quiz: {topic}",
            subject=subject,
            topic=topic,
            difficulty=difficulty,
            language=language
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)

        # Add questions (hard-limit to requested count)
        for q_data in (questions_data or [])[: max(1, int(num_questions or 1))]:
            question = QuizQuestion(
                quiz_id=quiz.id,
                question_text=q_data.get("question", ""),
                question_type="mcq",
                options=q_data.get("options", []),
                correct_answer=q_data.get("correct_answer", ""),
                explanation=q_data.get("explanation", ""),
                difficulty=difficulty,
                points=1
            )
            db.add(question)

        db.commit()
        db.refresh(quiz)

        return quiz

    def get_quiz(self, db: Session, quiz_id: int) -> Optional[Dict]:
        """Get quiz with questions"""
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            return None

        questions = db.query(QuizQuestion).filter(
            QuizQuestion.quiz_id == quiz_id
        ).all()

        return {
            "id": quiz.id,
            "title": quiz.title,
            "subject": quiz.subject,
            "topic": quiz.topic,
            "difficulty": quiz.difficulty,
            "language": quiz.language,
            "questions": [
                {
                    "id": q.id,
                    "question": q.question_text,
                    "type": q.question_type,
                    "options": q.options,
                    "points": q.points
                }
                for q in questions
            ],
            "total_points": sum(q.points for q in questions),
            "created_at": quiz.created_at.isoformat() if quiz.created_at else None
        }

    def submit_quiz(
        self,
        db: Session,
        student_id: int,
        quiz_id: int,
        responses: Dict[int, str],
        time_taken_seconds: int = 0
    ) -> Dict:
        """
        Submit and grade a quiz attempt

        Args:
            responses: Dict mapping question_id to answer
        """
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            return {"error": "Quiz not found"}

        questions = db.query(QuizQuestion).filter(
            QuizQuestion.quiz_id == quiz_id
        ).all()

        # Grade responses
        score = 0
        total_points = 0
        results = []
        weak_areas = []
        strong_areas = []

        for question in questions:
            total_points += question.points
            student_answer = responses.get(str(question.id), "")
            is_correct = student_answer.upper() == question.correct_answer.upper()

            if is_correct:
                score += question.points
                strong_areas.append(quiz.topic)
            else:
                weak_areas.append(quiz.topic)

            results.append({
                "question_id": question.id,
                "question": question.question_text,
                "your_answer": student_answer,
                "correct_answer": question.correct_answer,
                "is_correct": is_correct,
                "explanation": question.explanation,
                "points_earned": question.points if is_correct else 0
            })

        percentage = (score / total_points * 100) if total_points > 0 else 0

        # Create attempt record
        attempt = QuizAttempt(
            student_id=student_id,
            quiz_id=quiz_id,
            responses=responses,
            score=score,
            total_points=total_points,
            percentage=percentage,
            time_taken_seconds=time_taken_seconds,
            weak_areas=list(set(weak_areas)),
            strong_areas=list(set(strong_areas)),
            completed_at=datetime.utcnow()
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        # Update performance metrics
        if quiz.topic:
            student_profiler.update_performance_metric(
                db=db,
                student_id=student_id,
                subject=quiz.subject or "General",
                topic=quiz.topic,
                score=percentage
            )

        return {
            "attempt_id": attempt.id,
            "score": score,
            "total_points": total_points,
            "percentage": round(percentage, 2),
            "time_taken_seconds": time_taken_seconds,
            "results": results,
            "passed": percentage >= 60,
            "message": self._get_feedback_message(percentage)
        }

    def _get_feedback_message(self, percentage: float) -> str:
        """Get feedback message based on score"""
        if percentage >= 90:
            return "🎉 Excellent! You've mastered this topic!"
        elif percentage >= 80:
            return "👏 Great job! You have a strong understanding."
        elif percentage >= 70:
            return "👍 Good work! Keep practicing to improve."
        elif percentage >= 60:
            return "📚 You passed! Review the explanations to strengthen your knowledge."
        else:
            return "💪 Keep studying! Review the material and try again."

    def get_student_quiz_history(
        self,
        db: Session,
        student_id: int,
        limit: int = 10
    ) -> List[Dict]:
        """Get quiz history for a student"""
        attempts = db.query(QuizAttempt).filter(
            QuizAttempt.student_id == student_id
        ).order_by(QuizAttempt.started_at.desc()).limit(limit).all()

        history = []
        for attempt in attempts:
            quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
            history.append({
                "attempt_id": attempt.id,
                "quiz_id": attempt.quiz_id,
                "quiz_title": quiz.title if quiz else "Unknown",
                "topic": quiz.topic if quiz else None,
                "score": attempt.score,
                "total_points": attempt.total_points,
                "percentage": attempt.percentage,
                "time_taken": attempt.time_taken_seconds,
                "date": attempt.started_at.isoformat() if attempt.started_at else None
            })

        return history


# Singleton instance
quiz_generator = QuizGenerator()
