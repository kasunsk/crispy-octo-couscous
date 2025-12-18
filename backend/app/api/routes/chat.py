"""Chat and question answering API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid
from datetime import datetime
from pydantic import BaseModel

from app.models.database import get_db, ChatSession, ChatMessage, Document
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService
from app.services.search_service import SearchService
from app.services.embedding_service import EmbeddingService

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Initialize services
llm_service = LLMService()
embedding_service = EmbeddingService()
rag_service = RAGService(embedding_service, llm_service)
search_service = SearchService()


class QuestionRequest(BaseModel):
    """Question request model."""
    question: str
    document_id: Optional[str] = None
    session_id: Optional[str] = None
    use_internet: bool = False


class QuestionResponse(BaseModel):
    """Question response model."""
    answer: str
    sources: List[dict] = []
    session_id: str
    document_id: Optional[str] = None
    timestamp: str


class ChatMessageResponse(BaseModel):
    """Chat message response model."""
    id: str
    role: str
    content: str
    sources: Optional[List[dict]] = None
    created_at: str


@router.post("/question", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db)
):
    """Ask a question about a document or general question."""
    try:
        # Get or create session
        if request.session_id:
            try:
                session_id = uuid.UUID(request.session_id)
                session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
                if not session:
                    session = ChatSession(id=session_id)
                    db.add(session)
                    db.commit()
            except ValueError:
                session = ChatSession()
                db.add(session)
                db.commit()
        else:
            session = ChatSession()
            db.add(session)
            db.commit()
        
        # Save user message
        user_message = ChatMessage(
            session_id=session.id,
            document_id=uuid.UUID(request.document_id) if request.document_id else None,
            role="user",
            content=request.question
        )
        db.add(user_message)
        db.commit()
        
        # Determine answer source
        answer = ""
        sources = []
        document_id = None
        
        if request.document_id and not request.use_internet:
            # Document-based question
            try:
                doc_id = uuid.UUID(request.document_id)
                document = db.query(Document).filter(Document.id == doc_id).first()
                
                if not document:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Document not found"
                    )
                
                if document.status != "processed":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Document is still being processed"
                    )
                
                # Use RAG to answer
                result = rag_service.answer_question(
                    question=request.question,
                    document_id=request.document_id
                )
                
                answer = result["answer"]
                sources = result["sources"]
                document_id = request.document_id
            
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid document ID format"
                )
        
        else:
            # General question - use internet search
            try:
                # Search internet
                search_context = search_service.search_and_extract(
                    query=request.question,
                    num_sources=3
                )
                
                # Generate answer using LLM with search context
                answer = llm_service.generate_answer(
                    question=request.question,
                    context=search_context
                )
                
                # Get search results as sources
                search_results = search_service.search(request.question, max_results=3)
                sources = [
                    {
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "snippet": result.get("snippet", "")
                    }
                    for result in search_results
                ]
            
            except Exception as e:
                # Fallback to LLM without context
                answer = llm_service.generate_answer(question=request.question)
                sources = []
        
        # Save assistant message
        assistant_message = ChatMessage(
            session_id=session.id,
            document_id=uuid.UUID(document_id) if document_id else None,
            role="assistant",
            content=answer,
            sources=sources if sources else None
        )
        db.add(assistant_message)
        db.commit()
        
        return QuestionResponse(
            answer=answer,
            sources=sources,
            session_id=str(session.id),
            document_id=document_id,
            timestamp=datetime.utcnow().isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing question: {str(e)}"
        )


@router.get("/history/{session_id}", response_model=List[ChatMessageResponse])
async def get_chat_history(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get chat history for a session."""
    try:
        sess_id = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format"
        )
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == sess_id
    ).order_by(ChatMessage.created_at).all()
    
    return [
        ChatMessageResponse(
            id=str(msg.id),
            role=msg.role,
            content=msg.content,
            sources=msg.sources,
            created_at=msg.created_at.isoformat()
        )
        for msg in messages
    ]


@router.delete("/history/{session_id}")
async def delete_chat_history(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Delete a chat session."""
    try:
        sess_id = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format"
        )
    
    session = db.query(ChatSession).filter(ChatSession.id == sess_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    db.delete(session)
    db.commit()
    
    return {"message": "Chat history deleted successfully"}

