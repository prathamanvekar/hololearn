"""
RAG (Retrieval-Augmented Generation) Engine
============================================
Handles document indexing, retrieval, and context generation
"""

import os
from typing import List, Dict, Optional, Tuple, Any
import numpy as np

from backend.config import CHROMA_DIR, ModelConfig
from backend.modules.nlp_engine import nlp_engine


def _try_import_chromadb():
    """Import chromadb lazily.

    Chroma currently pulls in `pydantic.v1` which is not compatible with
    Python 3.14+ in some releases. Importing lazily lets the app boot and
    degrade gracefully when Chroma isn't available.
    """

    try:
        import chromadb  # type: ignore
        from chromadb.config import Settings  # type: ignore
        return chromadb, Settings, None
    except Exception as exc:  # noqa: BLE001 - we want to catch import-time issues
        return None, None, exc


class _NullCollection:
    def add(self, **kwargs: Any) -> None:  # noqa: ANN401
        return None

    def query(self, **kwargs: Any) -> Dict:  # noqa: ANN401
        return {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

    def get(self, **kwargs: Any) -> Dict:  # noqa: ANN401
        return {"ids": [], "metadatas": []}

    def delete(self, **kwargs: Any) -> None:  # noqa: ANN401
        return None


class RAGEngine:
    """
    RAG Engine using ChromaDB for vector storage
    and sentence-transformers for embeddings
    """

    def __init__(self):
        self.enabled = True
        self._init_error: Exception | None = None

        chromadb, Settings, import_error = _try_import_chromadb()
        if import_error is not None or chromadb is None or Settings is None:
            self.enabled = False
            self._init_error = import_error
            self.client = None
            self._document_collection = _NullCollection()
            self._quiz_collection = _NullCollection()
            print(
                "⚠️ ChromaDB is unavailable; RAG will run in degraded mode. "
                "(Document retrieval disabled)\n"
                f"   Reason: {import_error}"
            )
            return

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Create or get collections
        self._document_collection = None
        self._quiz_collection = None

        print("✅ RAG Engine initialized!")

    @property
    def document_collection(self):
        """Get or create document collection"""
        if not self.enabled:
            return self._document_collection

        if self._document_collection is None:
            self._document_collection = self.client.get_or_create_collection(
                name="documents",
                metadata={"description": "Student document chunks"}
            )
        return self._document_collection

    @property
    def quiz_collection(self):
        """Get or create quiz collection"""
        if not self.enabled:
            return self._quiz_collection

        if self._quiz_collection is None:
            self._quiz_collection = self.client.get_or_create_collection(
                name="quizzes",
                metadata={"description": "Quiz questions and answers"}
            )
        return self._quiz_collection

    def add_document_chunks(
        self,
        document_id: int,
        chunks: List[Dict],
        student_id: int,
        metadata: Dict = None
    ) -> List[str]:
        """
        Add document chunks to the vector store

        Args:
            document_id: Database document ID
            chunks: List of chunk dictionaries
            student_id: Student who owns the document
            metadata: Additional metadata

        Returns:
            List of chunk IDs
        """
        if not chunks:
            return []

        if not self.enabled:
            return []

        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:
            chunk_id = f"doc_{document_id}_chunk_{chunk['index']}"
            ids.append(chunk_id)
            documents.append(chunk['content'])

            chunk_metadata = {
                "document_id": document_id,
                "student_id": student_id,
                "chunk_index": chunk['index'],
                "word_count": chunk.get('word_count', 0)
            }

            if metadata:
                chunk_metadata.update(metadata)

            metadatas.append(chunk_metadata)

        # Generate embeddings
        embeddings = nlp_engine.get_embeddings(documents)

        # Add to collection
        self.document_collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings.tolist(),
            metadatas=metadatas
        )

        print(f"✅ Added {len(chunks)} chunks to vector store")

        return ids

    def search_documents(
        self,
        query: str,
        student_id: int = None,
        document_ids: List[int] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Search for relevant document chunks

        Args:
            query: Search query
            student_id: Filter by student (optional)
            document_ids: Filter by specific documents (optional)
            top_k: Number of results to return

        Returns:
            List of relevant chunks with scores
        """
        if not self.enabled:
            return []

        # Build filter
        where_filter = {}
        if student_id is not None:
            where_filter["student_id"] = student_id
        if document_ids:
            where_filter["document_id"] = {"$in": document_ids}

        # Generate query embedding
        query_embedding = nlp_engine.get_single_embedding(query)

        # Search
        results = self.document_collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            where=where_filter if where_filter else None,
            include=["documents", "metadatas", "distances"]
        )

        # Format results
        formatted_results = []
        if results['ids'] and results['ids'][0]:
            for i, chunk_id in enumerate(results['ids'][0]):
                formatted_results.append({
                    "chunk_id": chunk_id,
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i],
                    "relevance_score": 1 - results['distances'][0][i]  # Convert distance to similarity
                })

        return formatted_results

    def get_context_for_query(
        self,
        query: str,
        student_id: int = None,
        max_tokens: int = 2000,
        top_k: int = 5
    ) -> Tuple[str, List[Dict]]:
        """
        Get relevant context for a query (for RAG)

        Args:
            query: User query
            student_id: Filter by student
            max_tokens: Maximum context tokens
            top_k: Number of chunks to retrieve

        Returns:
            Tuple of (context_string, source_chunks)
        """
        # Search for relevant chunks
        chunks = self.search_documents(
            query=query,
            student_id=student_id,
            top_k=top_k
        )

        # Build context string
        context_parts = []
        total_tokens = 0
        included_chunks = []

        for chunk in chunks:
            # Rough token estimation (words * 1.3)
            chunk_tokens = len(chunk['content'].split()) * 1.3

            if total_tokens + chunk_tokens <= max_tokens:
                context_parts.append(chunk['content'])
                total_tokens += chunk_tokens
                included_chunks.append(chunk)
            else:
                break

        context_string = "\n\n---\n\n".join(context_parts)

        return context_string, included_chunks

    def delete_document(self, document_id: int):
        """Delete all chunks for a document"""
        if not self.enabled:
            return

        # Get all chunk IDs for this document
        results = self.document_collection.get(
            where={"document_id": document_id},
            include=["metadatas"]
        )

        if results['ids']:
            self.document_collection.delete(ids=results['ids'])
            print(f"✅ Deleted {len(results['ids'])} chunks for document {document_id}")

    def get_document_stats(self, student_id: int = None) -> Dict:
        """Get statistics about indexed documents"""
        if not self.enabled:
            return {
                "total_chunks": 0,
                "unique_documents": 0,
                "document_ids": [],
            }

        where_filter = {"student_id": student_id} if student_id else None

        results = self.document_collection.get(
            where=where_filter,
            include=["metadatas"]
        )

        total_chunks = len(results['ids']) if results['ids'] else 0

        # Count unique documents
        unique_docs = set()
        if results['metadatas']:
            for meta in results['metadatas']:
                if 'document_id' in meta:
                    unique_docs.add(meta['document_id'])

        return {
            "total_chunks": total_chunks,
            "unique_documents": len(unique_docs),
            "document_ids": list(unique_docs)
        }

    def clear_all(self):
        """Clear all data (use with caution)"""
        if not self.enabled:
            self._document_collection = _NullCollection()
            self._quiz_collection = _NullCollection()
            return

        self.client.delete_collection("documents")
        self.client.delete_collection("quizzes")
        self._document_collection = None
        self._quiz_collection = None
        print("⚠️ All RAG data cleared!")


# Singleton instance
rag_engine = RAGEngine()
