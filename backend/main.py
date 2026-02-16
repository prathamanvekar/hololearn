"""
HoloLearn Backend - Main Application
====================================
FastAPI application entry point
"""

# Allow running from inside the `backend/` folder (e.g. `uvicorn main:app`).
# In that case, Python's import path doesn't include the project root, so
# `import backend...` would fail unless we add it.
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.database.connection import init_db
from backend.routes import chat, documents, speech, profile, quiz, dashboard

# Create FastAPI app
app = FastAPI(
    title="HoloLearn API",
    description="AI-Driven Adaptive Holographic Learning Assistant",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(speech.router)
app.include_router(profile.router)
app.include_router(quiz.router)
app.include_router(dashboard.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("🚀 Starting HoloLearn Backend...")
    init_db()
    print("✅ HoloLearn Backend is ready!")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to HoloLearn API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
