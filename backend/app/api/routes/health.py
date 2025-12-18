"""Health check and system status API routes."""
from fastapi import APIRouter, HTTPException
from app.services.llm_service import LLMService
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["health"])

llm_service = LLMService()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    ollama_connected: bool
    available_models: List[str] = []


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check system health and connectivity."""
    try:
        ollama_connected = llm_service.check_connection()
        available_models = []
        
        if ollama_connected:
            available_models = llm_service.list_available_models()
        
        return HealthResponse(
            status="healthy" if ollama_connected else "degraded",
            ollama_connected=ollama_connected,
            available_models=available_models
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            ollama_connected=False,
            available_models=[]
        )

