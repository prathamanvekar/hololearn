"""
NLP Engine Module - ENHANCED VERSION
====================================
Now actually uses BERT/mBERT for:
- Intent Classification
- Language Detection
- Semantic Analysis
"""

import torch
from typing import List, Dict, Optional, Tuple
from transformers import (
    AutoTokenizer,
    AutoModel,
    AutoModelForSequenceClassification,
    pipeline,
    BertTokenizer,
    BertModel
)
from sentence_transformers import SentenceTransformer
import numpy as np

from backend.config import ModelConfig


class NLPEngine:
    """
    Enhanced NLP Engine using BERT/mBERT
    """

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🔧 NLP Engine using device: {self.device}")

        # Models - lazy loaded
        self._embedding_model = None
        self._mbert_tokenizer = None
        self._mbert_model = None
        self._zero_shot_classifier = None
        self._language_detector = None

        # Intent labels for classification
        self.intent_labels = [
            "asking a question about study material",
            "requesting an explanation of a concept",
            "asking for a summary",
            "requesting a quiz or test",
            "asking for translation",
            "requesting study recommendations",
            "greeting or casual conversation",
            "providing feedback",
            "other request"
        ]

    @property
    def embedding_model(self) -> SentenceTransformer:
        """Multilingual sentence transformer"""
        if self._embedding_model is None:
            print("📥 Loading Sentence Transformer model...")
            self._embedding_model = SentenceTransformer(
                ModelConfig.EMBEDDING_MODEL,
                device=self.device
            )
            print("✅ Sentence Transformer loaded!")
        return self._embedding_model

    @property
    def mbert_tokenizer(self):
        """mBERT tokenizer"""
        if self._mbert_tokenizer is None:
            print("📥 Loading mBERT tokenizer...")
            self._mbert_tokenizer = BertTokenizer.from_pretrained(
                ModelConfig.MBERT_MODEL
            )
            print("✅ mBERT tokenizer loaded!")
        return self._mbert_tokenizer

    @property
    def mbert_model(self):
        """mBERT model"""
        if self._mbert_model is None:
            print("📥 Loading mBERT model...")
            self._mbert_model = BertModel.from_pretrained(
                ModelConfig.MBERT_MODEL
            ).to(self.device)
            self._mbert_model.eval()
            print("✅ mBERT model loaded!")
        return self._mbert_model

    @property
    def zero_shot_classifier(self):
        """Zero-shot classifier using mBERT for intent detection"""
        if self._zero_shot_classifier is None:
            print("📥 Loading Zero-Shot Classifier...")
            self._zero_shot_classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",  # Works well for intent
                device=0 if self.device == "cuda" else -1
            )
            print("✅ Zero-Shot Classifier loaded!")
        return self._zero_shot_classifier

    @property
    def language_detector(self):
        """Language detection pipeline"""
        if self._language_detector is None:
            print("📥 Loading Language Detector...")
            self._language_detector = pipeline(
                "text-classification",
                model="papluca/xlm-roberta-base-language-detection",
                device=0 if self.device == "cuda" else -1
            )
            print("✅ Language Detector loaded!")
        return self._language_detector

    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using Sentence Transformer"""
        if not texts:
            return np.array([])

        embeddings = self.embedding_model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        return embeddings

    def get_single_embedding(self, text: str) -> np.ndarray:
        """Get embedding for single text"""
        return self.get_embeddings([text])[0]

    def get_mbert_embedding(self, text: str) -> np.ndarray:
        """
        Get BERT embedding using mBERT
        Returns [CLS] token representation
        """
        # Tokenize
        inputs = self.mbert_tokenizer(
            text,
            return_tensors="pt",
            max_length=512,
            truncation=True,
            padding=True
        ).to(self.device)

        # Get embeddings
        with torch.no_grad():
            outputs = self.mbert_model(**inputs)

        # Use [CLS] token embedding (first token)
        cls_embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()

        return cls_embedding[0]

    def get_mbert_contextual_embeddings(self, text: str) -> np.ndarray:
        """
        Get full contextual embeddings from mBERT
        Returns embeddings for all tokens
        """
        inputs = self.mbert_tokenizer(
            text,
            return_tensors="pt",
            max_length=512,
            truncation=True,
            padding=True
        ).to(self.device)

        with torch.no_grad():
            outputs = self.mbert_model(**inputs)

        # Return all token embeddings
        return outputs.last_hidden_state.cpu().numpy()[0]

    def classify_intent_with_bert(self, text: str) -> Dict[str, any]:
        """
        Classify intent using Zero-Shot Classification
        This ACTUALLY uses transformer models!
        """
        try:
            result = self.zero_shot_classifier(
                text,
                candidate_labels=self.intent_labels,
                multi_label=False
            )

            # Map to simple intent names
            intent_mapping = {
                "asking a question about study material": "question",
                "requesting an explanation of a concept": "explanation",
                "asking for a summary": "summary",
                "requesting a quiz or test": "quiz",
                "asking for translation": "translation",
                "requesting study recommendations": "recommendation",
                "greeting or casual conversation": "greeting",
                "providing feedback": "feedback",
                "other request": "other"
            }

            top_label = result["labels"][0]
            confidence = result["scores"][0]

            return {
                "intent": intent_mapping.get(top_label, "other"),
                "confidence": float(confidence),
                "raw_label": top_label,
                "all_scores": dict(zip(result["labels"], result["scores"]))
            }
        except Exception as e:
            print(f"⚠️ Zero-shot classification failed: {e}")
            # Fallback to keyword-based
            return self.classify_intent_keywords(text)

    def classify_intent_keywords(self, text: str) -> Dict[str, any]:
        """Fallback keyword-based intent classification"""
        text_lower = text.lower()

        patterns = {
            "question": ["what", "why", "how", "when", "where", "who", "which", "?"],
            "explanation": ["explain", "elaborate", "clarify", "describe", "tell me about"],
            "summary": ["summary", "summarize", "brief", "overview", "short version"],
            "quiz": ["quiz", "test", "question me", "assess", "exam"],
            "translation": ["translate", "in hindi", "in english", "convert to"],
            "recommendation": ["recommend", "suggest", "what should", "next topic"],
            "greeting": ["hello", "hi", "hey", "good morning", "good evening", "namaste"],
        }

        scores = {}
        for intent, keywords in patterns.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            scores[intent] = score

        if max(scores.values()) > 0:
            best_intent = max(scores, key=scores.get)
            confidence = min(scores[best_intent] / 3, 1.0)
        else:
            best_intent = "question"
            confidence = 0.5

        return {
            "intent": best_intent,
            "confidence": confidence,
            "all_scores": scores
        }

    def detect_language_with_bert(self, text: str) -> Dict[str, any]:
        """
        Detect language using XLM-RoBERTa model
        This ACTUALLY uses transformer models!
        """
        try:
            result = self.language_detector(text[:512])  # Limit length

            # Map model output to our language codes
            label = result[0]["label"]
            confidence = result[0]["score"]

            # The model returns language codes like "en", "hi", etc.
            return {
                "language": label.lower(),
                "confidence": float(confidence),
                "raw_result": result[0]
            }
        except Exception as e:
            print(f"⚠️ Language detection failed: {e}")
            return self._detect_language_heuristic(text)

    def _detect_language_heuristic(self, text: str) -> Dict[str, any]:
        """Fallback heuristic language detection"""
        # Count script characters
        devanagari = sum(1 for c in text if '\u0900' <= c <= '\u097F')
        tamil = sum(1 for c in text if '\u0B80' <= c <= '\u0BFF')
        telugu = sum(1 for c in text if '\u0C00' <= c <= '\u0C7F')
        bengali = sum(1 for c in text if '\u0980' <= c <= '\u09FF')

        total = len(text) or 1

        if devanagari / total > 0.3:
            return {"language": "hi", "confidence": 0.9}
        elif tamil / total > 0.3:
            return {"language": "ta", "confidence": 0.9}
        elif telugu / total > 0.3:
            return {"language": "te", "confidence": 0.9}
        elif bengali / total > 0.3:
            return {"language": "bn", "confidence": 0.9}
        else:
            return {"language": "en", "confidence": 0.8}

    def compute_semantic_similarity(
        self,
        text1: str,
        text2: str,
        use_mbert: bool = False
    ) -> float:
        """
        Compute semantic similarity between two texts
        Can use either Sentence Transformers or mBERT
        """
        if use_mbert:
            emb1 = self.get_mbert_embedding(text1)
            emb2 = self.get_mbert_embedding(text2)
        else:
            emb1 = self.get_single_embedding(text1)
            emb2 = self.get_single_embedding(text2)

        # Cosine similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        return float(similarity)

    def compute_similarity(
        self,
        query_embedding: np.ndarray,
        doc_embeddings: np.ndarray
    ) -> np.ndarray:
        """Compute cosine similarity between query and documents"""
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        doc_norms = doc_embeddings / np.linalg.norm(doc_embeddings, axis=1, keepdims=True)
        similarities = np.dot(doc_norms, query_norm)
        return similarities

    def find_similar_topics(
        self,
        query_topic: str,
        candidate_topics: List[str],
        top_k: int = 3,
        min_score: float = -1.0
    ) -> List[Tuple[str, float]]:
        """Return the most semantically similar topics to `query_topic`.

        This is used by the recommendation engine. It relies on the multilingual
        sentence-transformer embeddings already configured for the app.

        Args:
            query_topic: Topic string to compare against.
            candidate_topics: List of available topics.
            top_k: Max number of results.
            min_score: Optional minimum cosine similarity to include.

        Returns:
            List of tuples: (topic, similarity_score), sorted desc.
        """
        query = (query_topic or "").strip()
        if not query:
            return []

        candidates = [
            (t or "").strip() for t in (candidate_topics or [])
            if (t or "").strip() and (t or "").strip().lower() != query.lower()
        ]
        if not candidates:
            return []

        try:
            query_embedding = self.get_single_embedding(query)
            candidate_embeddings = self.get_embeddings(candidates)
            if candidate_embeddings is None or len(candidate_embeddings) == 0:
                return []

            similarities = self.compute_similarity(query_embedding, candidate_embeddings)
            ranked_indices = np.argsort(similarities)[::-1]

            results: List[Tuple[str, float]] = []
            for idx in ranked_indices[: max(1, int(top_k or 1))]:
                score = float(similarities[idx])
                if score >= float(min_score):
                    results.append((candidates[int(idx)], score))
            return results
        except Exception as e:
            print(f"⚠️ find_similar_topics failed: {e}")
            return []

    def extract_keywords_with_bert(self, text: str, top_k: int = 5) -> List[str]:
        """
        Extract keywords using BERT embeddings
        Finds words most similar to document meaning
        """
        # Get document embedding
        doc_embedding = self.get_mbert_embedding(text)

        # Tokenize and get word embeddings
        words = text.split()
        unique_words = list(set(w.strip('.,!?;:()[]{}"\'-').lower() for w in words))
        unique_words = [w for w in unique_words if len(w) > 3]

        if not unique_words:
            return []

        # Get embeddings for each word
        word_embeddings = self.get_embeddings(unique_words)

        # Compute similarity to document
        similarities = self.compute_similarity(doc_embedding, word_embeddings)

        # Get top-k
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        keywords = [unique_words[i] for i in top_indices]

        return keywords

    def analyze_text(self, text: str) -> Dict:
        """
        Complete text analysis using BERT models
        """
        return {
            "language": self.detect_language_with_bert(text),
            "intent": self.classify_intent_with_bert(text),
            "keywords": self.extract_keywords_with_bert(text),
            "embedding_shape": self.get_mbert_embedding(text).shape
        }


# Singleton instance
nlp_engine = NLPEngine()
