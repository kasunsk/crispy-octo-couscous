"""Simple fallback responses when Ollama is not available."""
import re
from typing import Optional


class SimpleFallback:
    """Simple rule-based fallback for when Ollama is unavailable."""
    
    GREETINGS = {
        "hi": "Hello! How can I help you today?",
        "hello": "Hi there! What would you like to know?",
        "hey": "Hey! How can I assist you?",
        "good morning": "Good morning! How can I help you?",
        "good afternoon": "Good afternoon! What can I do for you?",
        "good evening": "Good evening! How may I assist you?",
    }
    
    COMMON_RESPONSES = {
        "how are you": "I'm doing well, thank you for asking! How can I help you today?",
        "what can you do": "I can help you answer questions about uploaded documents or general questions. However, I need Ollama (a local AI service) to be running for full functionality.",
        "who are you": "I'm an AI assistant designed to help answer questions about documents and provide general information. I use local AI models through Ollama.",
    }
    
    @staticmethod
    def get_fallback_response(question: str) -> Optional[str]:
        """
        Get a simple fallback response for common questions.
        
        Args:
            question: User's question
        
        Returns:
            Fallback response or None if no match
        """
        question_lower = question.lower().strip()
        
        # Check greetings
        for greeting, response in SimpleFallback.GREETINGS.items():
            if greeting in question_lower:
                return response
        
        # Check common responses
        for pattern, response in SimpleFallback.COMMON_RESPONSES.items():
            if pattern in question_lower:
                return response
        
        # Default response
        return None
    
    @staticmethod
    def get_error_response() -> str:
        """Get a helpful error response when Ollama is not available."""
        return (
            "I apologize, but I'm currently unable to process your question because "
            "Ollama (the local AI service) is not running or not accessible.\n\n"
            "To fix this:\n"
            "1. Install Ollama from https://ollama.ai/download\n"
            "2. Pull a model: 'ollama pull llama3:8b'\n"
            "3. Make sure Ollama is running\n"
            "4. Refresh this page\n\n"
            "Once Ollama is running, I'll be able to answer your questions!"
        )


