"""
Document Processing Module
==========================
Handles PDF, DOCX, and Image (OCR) processing
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import PyPDF2
import pdfplumber
from docx import Document as DocxDocument
from PIL import Image
import pytesseract

from backend.config import UPLOAD_DIR, ModelConfig


class DocumentProcessor:
    """Process various document types and extract text"""

    def __init__(self):
        self.chunk_size = ModelConfig.CHUNK_SIZE
        self.chunk_overlap = ModelConfig.CHUNK_OVERLAP

    def process_file(self, file_path: str) -> Dict:
        """
        Process a file and extract text content

        Args:
            file_path: Path to the file

        Returns:
            Dict with extracted text and metadata
        """
        file_path = Path(file_path)
        file_extension = file_path.suffix.lower()

        try:
            if file_extension == '.pdf':
                return self._process_pdf(file_path)
            elif file_extension == '.docx':
                return self._process_docx(file_path)
            elif file_extension in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
                return self._process_image(file_path)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported file type: {file_extension}",
                    "text": "",
                    "chunks": [],
                    "metadata": {}
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "chunks": [],
                "metadata": {}
            }

    def _process_pdf(self, file_path: Path) -> Dict:
        """Process PDF file using pdfplumber for better extraction"""
        full_text = ""
        page_texts = []
        metadata = {
            "total_pages": 0,
            "file_type": "pdf"
        }

        try:
            # Try pdfplumber first (better for complex PDFs)
            with pdfplumber.open(file_path) as pdf:
                metadata["total_pages"] = len(pdf.pages)

                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    if text.strip():
                        page_texts.append({
                            "page": i + 1,
                            "text": text
                        })
                        full_text += f"\n[Page {i + 1}]\n{text}\n"

            # If pdfplumber fails, try PyPDF2
            if not full_text.strip():
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    metadata["total_pages"] = len(reader.pages)

                    for i, page in enumerate(reader.pages):
                        text = page.extract_text() or ""
                        if text.strip():
                            page_texts.append({
                                "page": i + 1,
                                "text": text
                            })
                            full_text += f"\n[Page {i + 1}]\n{text}\n"

            # Clean the text
            full_text = self._clean_text(full_text)

            # Create chunks
            chunks = self._create_chunks(full_text, page_texts)

            return {
                "success": True,
                "error": None,
                "text": full_text,
                "chunks": chunks,
                "metadata": metadata
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"PDF processing error: {str(e)}",
                "text": "",
                "chunks": [],
                "metadata": metadata
            }

    def _process_docx(self, file_path: Path) -> Dict:
        """Process DOCX file"""
        full_text = ""
        paragraphs = []
        metadata = {
            "file_type": "docx",
            "total_paragraphs": 0
        }

        try:
            doc = DocxDocument(file_path)

            for i, para in enumerate(doc.paragraphs):
                text = para.text.strip()
                if text:
                    paragraphs.append({
                        "index": i,
                        "text": text,
                        "style": para.style.name if para.style else "Normal"
                    })
                    full_text += text + "\n\n"

            # Also extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells)
                    if row_text.strip():
                        full_text += row_text + "\n"

            metadata["total_paragraphs"] = len(paragraphs)

            # Clean the text
            full_text = self._clean_text(full_text)

            # Create chunks
            chunks = self._create_chunks(full_text)

            return {
                "success": True,
                "error": None,
                "text": full_text,
                "chunks": chunks,
                "metadata": metadata
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"DOCX processing error: {str(e)}",
                "text": "",
                "chunks": [],
                "metadata": metadata
            }

    def _process_image(self, file_path: Path) -> Dict:
        """Process image file using OCR (Tesseract)"""
        metadata = {
            "file_type": "image",
            "ocr_engine": "tesseract"
        }

        try:
            # Open image
            image = Image.open(file_path)

            # Preprocess image for better OCR
            image = self._preprocess_image(image)

            # Perform OCR with multiple language support
            # eng = English, hin = Hindi (add more as needed)
            text = pytesseract.image_to_string(
                image,
                lang='eng+hin',
                config='--psm 6'  # Assume uniform block of text
            )

            # Clean the text
            text = self._clean_text(text)

            # Create chunks
            chunks = self._create_chunks(text)

            return {
                "success": True,
                "error": None,
                "text": text,
                "chunks": chunks,
                "metadata": metadata
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"OCR processing error: {str(e)}",
                "text": "",
                "chunks": [],
                "metadata": metadata
            }

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Convert to grayscale
        image = image.convert('L')

        # Resize if too small
        width, height = image.size
        if width < 1000:
            ratio = 1000 / width
            new_size = (int(width * ratio), int(height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        return image

    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\'\"\-\(\)\[\]\{\}\n]', '', text)

        return text.strip()

    def _create_chunks(
        self,
        text: str,
        page_texts: List[Dict] = None
    ) -> List[Dict]:
        """
        Split text into chunks for RAG

        Args:
            text: Full text to chunk
            page_texts: Optional list of page-wise text for metadata

        Returns:
            List of chunk dictionaries
        """
        chunks = []

        # Split by sentences first
        sentences = re.split(r'(?<=[.!?])\s+', text)

        current_chunk = ""
        current_length = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_length = len(sentence.split())

            if current_length + sentence_length <= self.chunk_size:
                current_chunk += " " + sentence
                current_length += sentence_length
            else:
                if current_chunk.strip():
                    chunks.append({
                        "index": chunk_index,
                        "content": current_chunk.strip(),
                        "word_count": current_length
                    })
                    chunk_index += 1

                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + " " + sentence
                current_length = len(current_chunk.split())

        # Add the last chunk
        if current_chunk.strip():
            chunks.append({
                "index": chunk_index,
                "content": current_chunk.strip(),
                "word_count": current_length
            })

        return chunks

    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from the end of a chunk"""
        words = text.split()
        overlap_words = words[-self.chunk_overlap:] if len(words) > self.chunk_overlap else words
        return " ".join(overlap_words)

    def get_file_info(self, file_path: str) -> Dict:
        """Get basic file information"""
        file_path = Path(file_path)

        return {
            "filename": file_path.name,
            "extension": file_path.suffix.lower(),
            "size_bytes": file_path.stat().st_size if file_path.exists() else 0,
            "exists": file_path.exists()
        }


# Singleton instance
document_processor = DocumentProcessor()
