"""
Speech Processing Module - ENHANCED VERSION
============================================
Actually uses Wav2Vec2 properly with fallbacks
"""

import os
import warnings
import torch
import librosa
import numpy as np
from typing import Dict, Optional
from transformers import (
    Wav2Vec2ForCTC,
    Wav2Vec2Processor,
    AutoProcessor,
    AutoModelForCTC,
    pipeline
)
import soundfile as sf

from backend.config import ModelConfig, AUDIO_TEMP_DIR


class SpeechProcessor:
    """
    Speech-to-text using Wav2Vec2
    Supports English and Hindi
    """

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🔧 Speech Processor using device: {self.device}")

        # Models - lazy loaded
        self._english_processor = None
        self._english_model = None
        self._hindi_processor = None
        self._hindi_model = None
        self._multilingual_processor = None
        self._multilingual_model = None
        self._whisper_en_pipeline = None
        self._whisper_multi_pipeline = None

        self.sample_rate = 16000

    @property
    def english_processor(self):
        """English Wav2Vec2 processor"""
        if self._english_processor is None:
            print("📥 Loading English Wav2Vec2...")
            self._english_processor = Wav2Vec2Processor.from_pretrained(
                "facebook/wav2vec2-base-960h"
            )
            print("✅ English Wav2Vec2 processor loaded!")
        return self._english_processor

    @property
    def english_model(self):
        """English Wav2Vec2 model"""
        if self._english_model is None:
            print("📥 Loading English Wav2Vec2 model...")
            self._english_model = Wav2Vec2ForCTC.from_pretrained(
                "facebook/wav2vec2-base-960h"
            ).to(self.device)
            self._english_model.eval()
            print("✅ English Wav2Vec2 model loaded!")
        return self._english_model

    @property
    def hindi_processor(self):
        """Hindi Wav2Vec2 processor"""
        if self._hindi_processor is None:
            print("📥 Loading Hindi Wav2Vec2...")
            try:
                # Use Vakyansh Hindi model
                self._hindi_processor = Wav2Vec2Processor.from_pretrained(
                    "ai4bharat/indicwav2vec-hindi"
                )
                print("✅ Hindi Wav2Vec2 processor loaded!")
            except Exception as e:
                print(f"⚠️ Hindi model not available: {e}")
                print("   Falling back to multilingual model...")
                self._hindi_processor = self.multilingual_processor
        return self._hindi_processor

    @property
    def hindi_model(self):
        """Hindi Wav2Vec2 model"""
        if self._hindi_model is None:
            try:
                print("📥 Loading Hindi Wav2Vec2 model...")
                self._hindi_model = Wav2Vec2ForCTC.from_pretrained(
                    "ai4bharat/indicwav2vec-hindi"
                ).to(self.device)
                self._hindi_model.eval()
                print("✅ Hindi Wav2Vec2 model loaded!")
            except Exception as e:
                print(f"⚠️ Hindi model not available: {e}")
                self._hindi_model = self.multilingual_model
        return self._hindi_model

    @property
    def multilingual_processor(self):
        """Multilingual Wav2Vec2 processor (fallback)"""
        if self._multilingual_processor is None:
            print("📥 Loading Multilingual Wav2Vec2...")
            self._multilingual_processor = AutoProcessor.from_pretrained(
                "facebook/wav2vec2-large-xlsr-53"
            )
            print("✅ Multilingual processor loaded!")
        return self._multilingual_processor

    @property
    def multilingual_model(self):
        """Multilingual Wav2Vec2 model (fallback)"""
        if self._multilingual_model is None:
            print("📥 Loading Multilingual Wav2Vec2 model...")
            self._multilingual_model = AutoModelForCTC.from_pretrained(
                "facebook/wav2vec2-large-xlsr-53"
            ).to(self.device)
            self._multilingual_model.eval()
            print("✅ Multilingual model loaded!")
        return self._multilingual_model

    @property
    def whisper_en_pipeline(self):
        """Whisper English fallback pipeline"""
        if self._whisper_en_pipeline is None:
            print("📥 Loading Whisper English fallback...")
            self._whisper_en_pipeline = pipeline(
                "automatic-speech-recognition",
                model="openai/whisper-tiny.en",
                device=0 if self.device == "cuda" else -1,
            )
            print("✅ Whisper English fallback loaded!")
        return self._whisper_en_pipeline

    @property
    def whisper_multi_pipeline(self):
        """Whisper multilingual fallback pipeline"""
        if self._whisper_multi_pipeline is None:
            print("📥 Loading Whisper multilingual fallback...")
            self._whisper_multi_pipeline = pipeline(
                "automatic-speech-recognition",
                model="openai/whisper-tiny",
                device=0 if self.device == "cuda" else -1,
            )
            print("✅ Whisper multilingual fallback loaded!")
        return self._whisper_multi_pipeline

    @staticmethod
    def _is_meaningful_text(text: str) -> bool:
        cleaned = (text or "").strip()
        if not cleaned:
            return False
        # Reject punctuation-only outputs like "..."
        return any(ch.isalnum() for ch in cleaned)

    def load_audio(self, file_path: str) -> tuple:
        """Load and preprocess audio"""
        try:
            # Prefer soundfile first (quiet and fast for common formats).
            try:
                audio, sr = sf.read(file_path, dtype="float32")
            except Exception:
                # Fallback for formats not handled by soundfile (e.g., some webm/opus).
                # Suppress known noisy warnings from librosa's deprecated audioread path.
                with warnings.catch_warnings():
                    warnings.filterwarnings(
                        "ignore",
                        message="PySoundFile failed. Trying audioread instead.*",
                        category=UserWarning,
                    )
                    warnings.filterwarnings(
                        "ignore",
                        message="librosa.core.audio.__audioread_load.*",
                        category=FutureWarning,
                    )
                    audio, sr = librosa.load(file_path, sr=None)

            # Ensure mono
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)

            # Resample if needed
            if sr != self.sample_rate:
                audio = librosa.resample(
                    audio,
                    orig_sr=sr,
                    target_sr=self.sample_rate
                )
                sr = self.sample_rate

            # Normalize
            audio = audio / (np.max(np.abs(audio)) + 1e-8)

            return audio, sr
        except Exception as e:
            raise Exception(f"Error loading audio: {str(e)}")

    def transcribe_english(self, audio_array: np.ndarray) -> str:
        """Transcribe English using Wav2Vec2"""
        # Process audio
        inputs = self.english_processor(
            audio_array,
            sampling_rate=self.sample_rate,
            return_tensors="pt",
            padding=True
        )

        input_values = inputs.input_values.to(self.device)

        # Inference
        with torch.no_grad():
            logits = self.english_model(input_values).logits

        # Decode
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = self.english_processor.batch_decode(predicted_ids)

        return transcription[0].lower()

    def transcribe_hindi(self, audio_array: np.ndarray) -> str:
        """Transcribe Hindi using Wav2Vec2"""
        try:
            inputs = self.hindi_processor(
                audio_array,
                sampling_rate=self.sample_rate,
                return_tensors="pt",
                padding=True
            )

            input_values = inputs.input_values.to(self.device)

            with torch.no_grad():
                logits = self.hindi_model(input_values).logits

            predicted_ids = torch.argmax(logits, dim=-1)
            transcription = self.hindi_processor.batch_decode(predicted_ids)

            return transcription[0]
        except Exception as e:
            print(f"⚠️ Hindi transcription failed: {e}")
            # Fallback to English model
            return self.transcribe_english(audio_array)

    def transcribe_with_whisper(self, audio_array: np.ndarray, language: str = "en") -> str:
        """Fallback transcription using Whisper models."""
        if language == "hi":
            out = self.whisper_multi_pipeline(
                {"array": audio_array, "sampling_rate": self.sample_rate},
                generate_kwargs={"language": "hi"}
            )
        else:
            out = self.whisper_en_pipeline(
                {"array": audio_array, "sampling_rate": self.sample_rate}
            )

        if isinstance(out, dict):
            return (out.get("text") or "").strip()
        return str(out or "").strip()

    def transcribe(
        self,
        file_path: str,
        language: str = "en"
    ) -> Dict[str, any]:
        """
        Transcribe audio file to text

        Args:
            file_path: Path to audio file
            language: 'en' for English, 'hi' for Hindi
        """
        try:
            # Load audio
            audio, sr = self.load_audio(file_path)
            duration = len(audio) / sr

            print(f"🎤 Transcribing {duration:.1f}s of audio in {language}...")

            # Transcribe with primary model first.
            primary_error = None
            try:
                if language == "hi":
                    text = self.transcribe_hindi(audio)
                else:
                    text = self.transcribe_english(audio)
                text = (text or "").strip()
                if not self._is_meaningful_text(text):
                    raise Exception("Wav2Vec2 produced empty/low-confidence text")

                print(f"✅ Transcription: {text[:100]}...")
                return {
                    "success": True,
                    "text": text,
                    "language": language,
                    "duration_seconds": round(duration, 2),
                    "model_used": f"wav2vec2-{language}"
                }
            except Exception as e:
                primary_error = str(e)
                print(f"⚠️ Primary STT failed, trying Whisper fallback: {primary_error}")

            # Whisper fallback
            fallback_text = self.transcribe_with_whisper(audio, language).strip()
            if self._is_meaningful_text(fallback_text):
                print(f"✅ Transcription (Whisper): {fallback_text[:100]}...")
                return {
                    "success": True,
                    "text": fallback_text,
                    "language": language,
                    "duration_seconds": round(duration, 2),
                    "model_used": f"whisper-{language}"
                }

            raise Exception(
                f"Could not detect clear speech from the audio (primary: {primary_error})"
            )

        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return {
                "success": False,
                "text": "",
                "error": str(e),
                "language": language
            }

    def transcribe_from_bytes(
        self,
        audio_bytes: bytes,
        language: str = "en",
        format: str = "wav"
    ) -> Dict[str, any]:
        """Transcribe from audio bytes"""
        import tempfile

        temp_path = os.path.join(AUDIO_TEMP_DIR, f"temp_audio.{format}")

        try:
            with open(temp_path, 'wb') as f:
                f.write(audio_bytes)

            result = self.transcribe(temp_path, language)

            if os.path.exists(temp_path):
                os.remove(temp_path)

            return result

        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)

            return {
                "success": False,
                "text": "",
                "error": str(e),
                "language": language
            }


# Singleton instance
speech_processor = SpeechProcessor()
