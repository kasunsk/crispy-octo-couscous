"""Chat and question answering API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid
from datetime import datetime
from pydantic import BaseModel
import logging

from app.models.database import get_db, ChatSession, ChatMessage, Document
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService
from app.services.search_service import SearchService
from app.services.embedding_service import EmbeddingService
from app.services.simple_fallback import SimpleFallback

logger = logging.getLogger(__name__)

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


def _needs_internet_search(question: str) -> bool:
    """Determine if a question needs internet search."""
    question_lower = question.lower().strip()
    
    # Questions that typically need current/up-to-date information
    # "Who is" questions often need current information (e.g., "who is the president")
    if question_lower.startswith("who is") or question_lower.startswith("who are"):
        return True
    
    # Keywords that suggest need for current/recent information
    internet_keywords = [
        "current", "latest", "recent", "today", "now", "2024", "2025",
        "news", "weather", "stock", "price", "rate", "what happened",
        "what is the current", "latest news", "recent events",
        "president", "prime minister", "leader", "ceo", "head of"
    ]
    return any(keyword in question_lower for keyword in internet_keywords)


def _get_conversation_history(session_id: uuid.UUID, db: Session, limit: int = 10) -> List[dict]:
    """Get recent conversation history for context."""
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.desc()).limit(limit).all()
    
    # Reverse to get chronological order
    messages.reverse()
    
    history = []
    for msg in messages:
        history.append({
            "role": msg.role,
            "content": msg.content
        })
    
    return history


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
        
        # Check if Ollama is available
        ollama_available = llm_service.check_connection()
        
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
                
                # Check if this is a summarization request
                question_lower = request.question.lower().strip()
                is_summarize_request = any(keyword in question_lower for keyword in [
                    "summarize", "summary", "summarise", "summaries",
                    "what is this document about", "what does this document say",
                    "overview", "brief", "key points", "main points"
                ])
                
                if is_summarize_request:
                    # Use summarization method (pass db for fallback)
                    result = rag_service.summarize_document(
                        document_id=request.document_id,
                        db=db
                    )
                else:
                    # Use RAG to answer specific question
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
            # General question - prioritize conversational LLM chat
            try:
                if ollama_available:
                    # Get conversation history for context
                    history = _get_conversation_history(session.id, db, limit=10)
                    
                    # Build messages list for chat API
                    messages = []
                    
                    # Add system message
                    messages.append({
                        "role": "system",
                        "content": "You are a helpful, friendly AI assistant. You engage in natural conversations and provide helpful, accurate information. Be conversational and engaging, like ChatGPT or DeepSeek."
                    })
                    
                    # Add conversation history
                    for msg in history:
                        messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
                    
                    # Add current question
                    messages.append({
                        "role": "user",
                        "content": request.question
                    })
                    
                    # Determine if internet search is needed
                    needs_search = _needs_internet_search(request.question) or request.use_internet
                    
                    if needs_search:
                        # Search internet for context
                        try:
                            search_context = search_service.search_and_extract(
                                query=request.question,
                                num_sources=3
                            )
                            
                            # Get search results as sources
                            search_results = search_service.search(request.question, max_results=3)
                            
                            if search_context and search_results:
                                # Add search context to the last user message
                                messages[-1]["content"] = f"{request.question}\n\nContext from web search:\n{search_context}\n\nPlease provide an accurate, up-to-date answer based on the search results above."
                                sources = [
                                    {
                                        "title": result.get("title", ""),
                                        "url": result.get("url", ""),
                                        "snippet": result.get("snippet", "")
                                    }
                                    for result in search_results
                                ]
                            elif search_results:
                                # We have results but couldn't extract full content, use snippets
                                messages[-1]["content"] = f"{request.question}\n\nSearch results:\n" + "\n".join([
                                    f"- {r.get('title', '')}: {r.get('snippet', '')}" 
                                    for r in search_results[:3]
                                ]) + "\n\nPlease provide an accurate answer based on these search results."
                                sources = [
                                    {
                                        "title": result.get("title", ""),
                                        "url": result.get("url", ""),
                                        "snippet": result.get("snippet", "")
                                    }
                                    for result in search_results
                                ]
                            else:
                                # Search failed - inform LLM to use its knowledge but note search wasn't available
                                messages[-1]["content"] = f"{request.question}\n\nNote: Web search was attempted but is currently unavailable (possibly due to rate limits). Please provide the best answer you can based on your training data, but note that the information may not be current."
                                logger.warning(f"Internet search returned no results for: {request.question}")
                                sources = []
                        except Exception as e:
                            logger.warning(f"Internet search failed: {str(e)}, continuing with LLM only")
                            # Inform LLM that search failed
                            messages[-1]["content"] = f"{request.question}\n\nNote: Web search was attempted but failed. Please provide the best answer you can based on your training data, but note that the information may not be current."
                            sources = []
                    
                    # Generate answer using chat API with conversation history
                    answer = llm_service.chat(messages=messages)
                    
                else:
                    # Ollama not available - try fallback
                    fallback_response = SimpleFallback.get_fallback_response(request.question)
                    if fallback_response:
                        answer = fallback_response
                        sources = []
                    else:
                        answer = SimpleFallback.get_error_response()
                        sources = []
            
            except Exception as e:
                # Check if it's an Ollama connection error
                error_msg = str(e)
                if "Ollama is not running" in error_msg or "Connection refused" in error_msg or "111" in error_msg:
                    # Try simple fallback first
                    fallback_response = SimpleFallback.get_fallback_response(request.question)
                    if fallback_response:
                        answer = fallback_response
                        sources = []
                    else:
                        answer = SimpleFallback.get_error_response()
                        sources = []
                else:
                    # Try fallback
                    fallback_response = SimpleFallback.get_fallback_response(request.question)
                    if fallback_response:
                        answer = fallback_response
                        sources = []
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail=f"AI service unavailable: {str(e)}"
                        )
        
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

