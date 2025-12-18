"""Document management API routes."""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
import os
from pathlib import Path
from datetime import datetime

from app.models.database import get_db, Document, DocumentChunk
from app.services.document_processor import DocumentProcessor
from app.services.embedding_service import EmbeddingService
from app.utils.chunking import chunk_text
from pydantic import BaseModel

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Initialize services
upload_dir = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(upload_dir, exist_ok=True)

doc_processor = DocumentProcessor(upload_dir=upload_dir)
embedding_service = EmbeddingService()


class DocumentResponse(BaseModel):
    """Document response model."""
    id: str
    filename: str
    file_type: str
    file_size: int
    chunks_count: int
    status: str
    uploaded_at: str
    processed_at: str | None

    class Config:
        from_attributes = True


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process a document."""
    try:
        # Validate file type
        if not doc_processor.is_supported(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Supported: PDF, Excel, Word"
            )
        
        # Generate unique filename
        file_id = uuid.uuid4()
        file_ext = Path(file.filename).suffix
        saved_filename = f"{file_id}{file_ext}"
        file_path = Path(upload_dir) / saved_filename
        
        # Save file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        file_size = len(content)
        file_info = doc_processor.get_file_info(str(file_path))
        
        # Create document record
        document = Document(
            id=file_id,
            filename=file.filename,
            file_type=file_info["file_type"],
            file_path=str(file_path),
            file_size=file_size,
            status="processing"
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Process document asynchronously (in production, use background tasks)
        try:
            # Extract text
            text_content = doc_processor.extract_text(str(file_path), file_info["file_type"])
            
            # Chunk text
            chunks = chunk_text(text_content, chunk_size=1000, overlap=200)
            
            # Save chunks to database
            for chunk in chunks:
                db_chunk = DocumentChunk(
                    document_id=file_id,
                    chunk_index=chunk["chunk_index"],
                    content=chunk["content"],
                    start_char=chunk.get("start_char"),
                    end_char=chunk.get("end_char"),
                    metadata=chunk.get("metadata")
                )
                db.add(db_chunk)
            
            # Generate embeddings and store in vector DB
            collection_name = f"documents_{file_id}"
            embedding_service.add_document_chunks(
                collection_name=collection_name,
                chunks=chunks,
                document_id=str(file_id),
                filename=file.filename,
                file_type=file_info["file_type"]
            )
            
            # Update document status
            document.status = "processed"
            document.chunks_count = len(chunks)
            document.processed_at = datetime.utcnow()
            db.commit()
        
        except Exception as e:
            # Mark as failed
            document.status = "failed"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process document: {str(e)}"
            )
        
        return DocumentResponse(
            id=str(document.id),
            filename=document.filename,
            file_type=document.file_type,
            file_size=document.file_size,
            chunks_count=document.chunks_count,
            status=document.status,
            uploaded_at=document.uploaded_at.isoformat(),
            processed_at=document.processed_at.isoformat() if document.processed_at else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}"
        )


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all documents."""
    documents = db.query(Document).offset(skip).limit(limit).all()
    return [
        DocumentResponse(
            id=str(doc.id),
            filename=doc.filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            chunks_count=doc.chunks_count,
            status=doc.status,
            uploaded_at=doc.uploaded_at.isoformat(),
            processed_at=doc.processed_at.isoformat() if doc.processed_at else None
        )
        for doc in documents
    ]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific document."""
    try:
        doc_id = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )
    
    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentResponse(
        id=str(document.id),
        filename=document.filename,
        file_type=document.file_type,
        file_size=document.file_size,
        chunks_count=document.chunks_count,
        status=document.status,
        uploaded_at=document.uploaded_at.isoformat(),
        processed_at=document.processed_at.isoformat() if document.processed_at else None
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Delete a document and its chunks."""
    try:
        doc_id = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )
    
    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete from vector DB
    try:
        collection_name = f"documents_{document_id}"
        embedding_service.delete_document(collection_name, str(doc_id))
    except Exception as e:
        pass  # Continue even if vector DB deletion fails
    
    # Delete file
    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
    except Exception as e:
        pass  # Continue even if file deletion fails
    
    # Delete from database (cascade will delete chunks)
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}


@router.get("/{document_id}/chunks")
async def get_document_chunks(
    document_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get chunks for a document."""
    try:
        doc_id = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )
    
    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == doc_id
    ).offset(skip).limit(limit).all()
    
    return [
        {
            "id": str(chunk.id),
            "chunk_index": chunk.chunk_index,
            "content": chunk.content[:500] + "..." if len(chunk.content) > 500 else chunk.content,
            "metadata": chunk.metadata
        }
        for chunk in chunks
    ]

