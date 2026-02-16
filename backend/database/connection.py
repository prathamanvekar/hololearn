"""
Database Connection Module
==========================
Handles SQLite database connection using SQLAlchemy
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.config import DATABASE_URL

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    from backend.database.models import (
        Student, Document, DocumentChunk,
        Quiz, QuizQuestion, QuizAttempt,
        LearningSession, PerformanceMetric
    )
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully!")
