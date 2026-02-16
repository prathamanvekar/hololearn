"""
HoloLearn Configuration
=======================
Central configuration for all modules
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma_db"
AUDIO_TEMP_DIR = BASE_DIR / "backend" / "audio_temp"

# Create directories if they don't exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Database
DATABASE_URL = f"sqlite:///{DATA_DIR}/hololearn.db"

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your-groq-api-key-here")

# Model Configurations
class ModelConfig:
    # Speech Recognition (Wav2Vec2)
    WAV2VEC2_MODEL = "facebook/wav2vec2-base-960h"
    WAV2VEC2_MODEL_HINDI = "ai4bharat/indicwav2vec-hindi"

    # NLP Models (BERT/mBERT)
    MBERT_MODEL = "bert-base-multilingual-cased"
    INDICBERT_MODEL = "ai4bharat/indic-bert"

    # Sentence Embeddings
    EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # Groq LLM
    GROQ_MODEL = "llama-3.1-8b-instant"

    # Chunk Settings for RAG
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50

# Supported Languages
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi"
}

# Default Language
DEFAULT_LANGUAGE = "en"
SECONDARY_LANGUAGE = "hi"  # Hindi as default secondary

# Quiz Settings
QUIZ_QUESTIONS_PER_SESSION = 5
QUIZ_TIME_LIMIT_MINUTES = 10

# Avatar Settings
AVATAR_SPEAKING_SPEED = 1.0
