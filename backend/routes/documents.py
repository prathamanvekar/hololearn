"""
Document Routes
===============
Handles document upload and processing
"""

import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from backend.database.connection import get_db
from backend.database.models import Document, DocumentChunk
from backend.modules.document_processor import document_processor
from backend.modules.rag_engine import rag_engine
from backend.config import UPLOAD_DIR

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    student_id: int = Form(...),
    title: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    topic: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload and process a document
    """
    # Validate file type
    allowed_extensions = ['.pdf', '.docx', '.doc', '.png', '.jpg', '.jpeg', '.bmp', '.tiff']
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}"
        )

    # Create student directory
    student_dir = UPLOAD_DIR / str(student_id)
    student_dir.mkdir(parents=True, exist_ok=True)

    # Save file
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = student_dir / safe_filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Get file size
    file_size = os.path.getsize(file_path)

    # Create document record
    document = Document(
        student_id=student_id,
        filename=file.filename,
        file_type=file_extension.replace('.', ''),
        file_path=str(file_path),
        file_size=file_size,
        title=title or file.filename,
        subject=subject,
        topic=topic,
        is_processed=False
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Process document
    try:
        result = document_processor.process_file(str(file_path))

        if result["success"]:
            # Add chunks to database and RAG
            chunk_ids = rag_engine.add_document_chunks(
                document_id=document.id,
                chunks=result["chunks"],
                student_id=student_id,
                metadata={
                    "filename": file.filename,
                    "subject": subject,
                    "topic": topic
                }
            )

            # Save chunks to database
            for i, chunk in enumerate(result["chunks"]):
                db_chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_index=chunk["index"],
                    content=chunk["content"],
                    embedding_id=chunk_ids[i] if i < len(chunk_ids) else None
                )
                db.add(db_chunk)

            document.is_processed = True
            db.commit()

            return {
                "success": True,
                "document_id": document.id,
                "filename": file.filename,
                "chunks_created": len(result["chunks"]),
                "message": "Document uploaded and processed successfully"
            }
        else:
            document.processing_error = result.get("error", "Unknown error")
            db.commit()

            return {
                "success": False,
                "document_id": document.id,
                "filename": file.filename,
                "error": result.get("error"),
                "message": "Document uploaded but processing failed"
            }

    except Exception as e:
        document.processing_error = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/list/{student_id}")
async def list_documents(student_id: int, db: Session = Depends(get_db)):
    """
    List all documents for a student
    """
    documents = db.query(Document).filter(
        Document.student_id == student_id
    ).order_by(Document.created_at.desc()).all()

    return {
        "documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "title": doc.title,
                "subject": doc.subject,
                "topic": doc.topic,
                "file_type": doc.file_type,
                "file_size": doc.file_size,
                "is_processed": doc.is_processed,
                "created_at": doc.created_at.isoformat() if doc.created_at else None
            }
            for doc in documents
        ]
    }


@router.get("/{document_id}")
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """
    Get document details
    """
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get chunk count
    chunk_count = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).count()

    return {
        "id": document.id,
        "filename": document.filename,
        "title": document.title,
        "subject": document.subject,
        "topic": document.topic,
        "file_type": document.file_type,
        "file_size": document.file_size,
        "is_processed": document.is_processed,
        "processing_error": document.processing_error,
        "chunk_count": chunk_count,
        "created_at": document.created_at.isoformat() if document.created_at else None
    }


@router.delete("/{document_id}")
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """
    Delete a document
    """
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete from RAG
    rag_engine.delete_document(document_id)

    # Delete file
    if document.file_path and os.path.exists(document.file_path):
        os.remove(document.file_path)

    # Delete from database
    db.delete(document)
    db.commit()

    return {"message": "Document deleted successfully"}


@router.post("/search")
async def search_documents(
    query: str,
    student_id: int,
    top_k: int = 5,
    db: Session = Depends(get_db)
):
    """
    Search through documents
    """
    results = rag_engine.search_documents(
        query=query,
        student_id=student_id,
        top_k=top_k
    )

    return {
        "query": query,
        "results": results
    }
