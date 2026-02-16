"""
Database Models
===============
SQLAlchemy models for HoloLearn
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float,
    DateTime, Boolean, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from backend.database.connection import Base


class Student(Base):
    """Student profile model"""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True)
    preferred_language = Column(String(10), default="en")
    secondary_language = Column(String(10), default="hi")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Learning preferences (JSON)
    preferences = Column(JSON, default={})

    # Relationships
    documents = relationship("Document", back_populates="student")
    quiz_attempts = relationship("QuizAttempt", back_populates="student")
    learning_sessions = relationship("LearningSession", back_populates="student")
    performance_metrics = relationship("PerformanceMetric", back_populates="student")

    def __repr__(self):
        return f"<Student(id={self.id}, name={self.name})>"


class Document(Base):
    """Uploaded document model"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50))  # pdf, docx, image
    file_path = Column(String(500))
    file_size = Column(Integer)

    # Metadata
    title = Column(String(255))
    subject = Column(String(100))
    topic = Column(String(100))
    language = Column(String(10), default="en")

    # Processing status
    is_processed = Column(Boolean, default=False)
    processing_error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename})>"


class DocumentChunk(Base):
    """Document chunks for RAG"""
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    chunk_index = Column(Integer)
    content = Column(Text, nullable=False)

    # Metadata for retrieval
    page_number = Column(Integer, nullable=True)
    section = Column(String(255), nullable=True)

    # Vector embedding ID (reference to ChromaDB)
    embedding_id = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="chunks")

    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, doc_id={self.document_id})>"


class Quiz(Base):
    """Quiz model"""
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    subject = Column(String(100))
    topic = Column(String(100))
    difficulty = Column(String(20), default="medium")  # easy, medium, hard
    language = Column(String(10), default="en")

    # Source document (if generated from document)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="quiz")

    def __repr__(self):
        return f"<Quiz(id={self.id}, title={self.title})>"


class QuizQuestion(Base):
    """Quiz question model"""
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    question_text = Column(Text, nullable=False)
    question_type = Column(String(20), default="mcq")  # mcq, true_false, short_answer

    # Options (JSON array for MCQ)
    options = Column(JSON, nullable=True)
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)

    # Difficulty and points
    difficulty = Column(String(20), default="medium")
    points = Column(Integer, default=1)

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")

    def __repr__(self):
        return f"<QuizQuestion(id={self.id}, quiz_id={self.quiz_id})>"


class QuizAttempt(Base):
    """Quiz attempt model"""
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))

    # Responses (JSON: {question_id: answer})
    responses = Column(JSON, default={})

    # Results
    score = Column(Float, default=0.0)
    total_points = Column(Integer, default=0)
    percentage = Column(Float, default=0.0)
    time_taken_seconds = Column(Integer, default=0)

    # Analysis
    weak_areas = Column(JSON, default=[])
    strong_areas = Column(JSON, default=[])

    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    student = relationship("Student", back_populates="quiz_attempts")
    quiz = relationship("Quiz", back_populates="attempts")

    def __repr__(self):
        return f"<QuizAttempt(id={self.id}, score={self.score})>"


class LearningSession(Base):
    """Learning session tracking"""
    __tablename__ = "learning_sessions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))

    # Session details
    session_type = Column(String(50))  # chat, quiz, document_study
    topic = Column(String(100), nullable=True)
    subject = Column(String(100), nullable=True)

    # Interaction data
    queries = Column(JSON, default=[])  # List of queries in session
    duration_minutes = Column(Integer, default=0)

    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    # Relationships
    student = relationship("Student", back_populates="learning_sessions")

    def __repr__(self):
        return f"<LearningSession(id={self.id}, type={self.session_type})>"


class PerformanceMetric(Base):
    """Student performance metrics"""
    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))

    # Metric details
    subject = Column(String(100))
    topic = Column(String(100))

    # Scores
    average_score = Column(Float, default=0.0)
    total_attempts = Column(Integer, default=0)
    improvement_rate = Column(Float, default=0.0)

    # Mastery level (0-100)
    mastery_level = Column(Float, default=0.0)

    # Time tracking
    total_study_time_minutes = Column(Integer, default=0)

    last_activity = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="performance_metrics")

    def __repr__(self):
        return f"<PerformanceMetric(id={self.id}, subject={self.subject})>"


class ChatHistory(Base):
    """Chat history for context"""
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    session_id = Column(String(100))

    role = Column(String(20))  # user, assistant
    content = Column(Text, nullable=False)
    language = Column(String(10), default="en")

    # Metadata
    intent = Column(String(50), nullable=True)
    referenced_documents = Column(JSON, default=[])

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ChatHistory(id={self.id}, role={self.role})>"
