"""
Speech Routes
=============
Handles speech-to-text processing
"""

import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional

from backend.database.connection import get_db
from backend.modules.speech_processor import speech_processor
from backend.config import AUDIO_TEMP_DIR

router = APIRouter(prefix="/speech", tags=["Speech"])


@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: Optional[str] = Form("en"),
    db: Session = Depends(get_db)
):
    """
    Transcribe audio file to text using Wav2Vec2
    """
    # Validate file type
    allowed_extensions = ['.wav', '.mp3', '.ogg', '.flac', '.m4a', '.webm']
    file_extension = os.path.splitext(audio.filename)[1].lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Audio format not supported. Allowed: {', '.join(allowed_extensions)}"
        )

    # Save temporary file
    temp_path = AUDIO_TEMP_DIR / f"temp_{audio.filename}"

    try:
        with open(temp_path, "wb") as buffer:
            content = await audio.read()
            buffer.write(content)

        # Transcribe
        result = speech_processor.transcribe(str(temp_path), language)

        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if result["success"]:
            return {
                "success": True,
                "text": result["text"],
                "language": result["language"],
                "duration_seconds": result.get("duration_seconds", 0)
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Transcription failed")
            )

    except Exception as e:
        # Clean up on error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe-bytes")
async def transcribe_audio_bytes(
    audio_bytes: bytes,
    language: str = "en",
    format: str = "wav"
):
    """
    Transcribe audio from bytes (for real-time processing)
    """
    result = speech_processor.transcribe_from_bytes(
        audio_bytes=audio_bytes,
        language=language,
        format=format
    )

    if result["success"]:
        return {
            "success": True,
            "text": result["text"],
            "language": result["language"]
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Transcription failed")
        )
