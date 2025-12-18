"""LLM service for interacting with local Ollama models."""
import httpx
import os
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with local LLM via Ollama."""
    
    def __init__(self, base_url: Optional[str] = None, model_name: str = "llama3:8b"):
        """
        Initialize LLM service.
        
        Args:
            base_url: Ollama base URL (default: http://localhost:11434)
            model_name: Name of the model to use
        """
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = model_name or os.getenv("OLLAMA_MODEL", "llama3:8b")
        self.client = httpx.Client(base_url=self.base_url, timeout=120.0)
        
        logger.info(f"LLM Service initialized with model: {self.model_name}")
    
    def generate_answer(
        self,
        question: str,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate answer to a question, optionally with context.
        
        Args:
            question: User's question
            context: Optional context from documents
            system_prompt: Optional system prompt
        
        Returns:
            Generated answer
        """
        try:
            # Build prompt
            if context:
                prompt = self._build_rag_prompt(question, context, system_prompt)
            else:
                prompt = question
            
            # Default system prompt
            if not system_prompt:
                system_prompt = self._get_default_system_prompt()
            
            # Generate response using Ollama API
            response = self.client.post(
                "/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "system": system_prompt,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                    },
                    "stream": False
                }
            )
            response.raise_for_status()
            result = response.json()
            
            return result.get("response", "").strip()
        
        except httpx.ConnectError as e:
            error_msg = str(e)
            if "Connection refused" in error_msg or "111" in error_msg:
                logger.error(f"Ollama connection refused. Is Ollama running at {self.base_url}?")
                raise Exception(
                    f"Ollama is not running or not accessible at {self.base_url}. "
                    f"Please install and start Ollama, then pull a model (e.g., 'ollama pull llama3:8b'). "
                    f"See OLLAMA_SETUP.md for instructions."
                )
            else:
                logger.error(f"Ollama connection error: {str(e)}")
                raise Exception(f"Failed to connect to Ollama: {str(e)}")
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            raise Exception(f"Failed to generate answer: {str(e)}")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Chat with the model using message history.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt
        
        Returns:
            Model response
        """
        try:
            if not system_prompt:
                system_prompt = self._get_default_system_prompt()
            
            response = self.client.post(
                "/api/chat",
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                    },
                    "stream": False
                }
            )
            response.raise_for_status()
            result = response.json()
            
            return result.get("message", {}).get("content", "").strip()
        
        except httpx.ConnectError as e:
            error_msg = str(e)
            if "Connection refused" in error_msg or "111" in error_msg:
                logger.error(f"Ollama connection refused. Is Ollama running at {self.base_url}?")
                raise Exception(
                    f"Ollama is not running or not accessible at {self.base_url}. "
                    f"Please install and start Ollama, then pull a model (e.g., 'ollama pull llama3:8b'). "
                    f"See OLLAMA_SETUP.md for instructions."
                )
            else:
                logger.error(f"Ollama connection error: {str(e)}")
                raise Exception(f"Failed to connect to Ollama: {str(e)}")
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            raise Exception(f"Failed to chat: {str(e)}")
    
    def _build_rag_prompt(self, question: str, context: str, system_prompt: Optional[str] = None) -> str:
        """Build RAG prompt with context."""
        prompt = f"""Context:
{context}

Question: {question}

Instructions:
- Answer the question based on the provided context above.
- If the answer cannot be found in the context, say "I cannot find this information in the provided document."
- Be accurate, concise, and cite specific details from the context when possible.
- If the question asks for a list (like "all degrees"), make sure to include all items mentioned in the context.
"""
        return prompt
    
    def _get_default_system_prompt(self) -> str:
        """Get default system prompt."""
        return """You are a helpful AI assistant that answers questions based on provided documents. 
You are accurate, concise, and always cite information from the source material when available.
If you don't know something, say so clearly."""
    
    def list_available_models(self) -> List[str]:
        """List available models in Ollama."""
        try:
            response = self.client.get("/api/tags")
            response.raise_for_status()
            result = response.json()
            return [model["name"] for model in result.get("models", [])]
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return []
    
    def check_connection(self) -> bool:
        """Check if Ollama is accessible."""
        try:
            response = self.client.get("/api/tags", timeout=5.0)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"Ollama connection check failed: {str(e)}")
            return False

