"""
Translator Module
=================
Handles bilingual translation using LLM
"""

from typing import Dict, Optional
from backend.modules.llm_service import llm_service
from backend.config import SUPPORTED_LANGUAGES


class Translator:
    """
    Translation service using Groq LLM
    """

    def __init__(self):
        print("✅ Translator initialized!")

    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """
        Translate text between languages
        """
        if source_lang == target_lang:
            return text

        return llm_service.translate_text(text, source_lang, target_lang)

    def get_bilingual_text(
        self,
        text: str,
        primary_lang: str = "en",
        secondary_lang: str = "hi"
    ) -> Dict[str, str]:
        """
        Get text in both languages
        """
        result = {
            primary_lang: text,
            secondary_lang: ""
        }

        # Detect if text is already in secondary language
        if self._is_language(text, secondary_lang):
            result[secondary_lang] = text
            result[primary_lang] = self.translate(text, secondary_lang, primary_lang)
        else:
            result[secondary_lang] = self.translate(text, primary_lang, secondary_lang)

        return result

    def _is_language(self, text: str, lang_code: str) -> bool:
        """
        Simple check if text is in a specific language
        """
        # Check for Devanagari (Hindi)
        if lang_code == "hi":
            devanagari_count = sum(1 for c in text if '\u0900' <= c <= '\u097F')
            return devanagari_count > len(text) * 0.3

        # Check for Tamil
        if lang_code == "ta":
            tamil_count = sum(1 for c in text if '\u0B80' <= c <= '\u0BFF')
            return tamil_count > len(text) * 0.3

        # Default to False for English and others
        return False

    def detect_language(self, text: str) -> str:
        """
        Detect the language of text
        """
        from backend.modules.nlp_engine import nlp_engine
        result = nlp_engine.detect_language(text)
        return result["language"]

    def get_supported_languages(self) -> Dict[str, str]:
        """Get list of supported languages"""
        return SUPPORTED_LANGUAGES


# Singleton instance
translator = Translator()
