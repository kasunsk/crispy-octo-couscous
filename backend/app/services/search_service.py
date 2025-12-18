"""Internet search service for general queries."""
from duckduckgo_search import DDGS
from typing import List, Dict, Optional
import logging
import requests
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


class SearchService:
    """Service for searching the internet and extracting information."""
    
    def __init__(self, max_results: int = 5):
        """
        Initialize search service.
        
        Args:
            max_results: Maximum number of search results to return
        """
        self.max_results = max_results
        logger.info("Search service initialized")
    
    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict]:
        """
        Search the internet for a query.
        
        Args:
            query: Search query
            max_results: Maximum number of results (overrides default)
        
        Returns:
            List of search results with title, url, and snippet
        """
        if max_results is None:
            max_results = self.max_results
        
        try:
            results = []
            with DDGS() as ddgs:
                search_results = ddgs.text(
                    query,
                    max_results=max_results
                )
                
                for result in search_results:
                    results.append({
                        "title": result.get("title", ""),
                        "url": result.get("href", ""),
                        "snippet": result.get("body", "")
                    })
            
            logger.info(f"Found {len(results)} search results for query: {query}")
            return results
        
        except Exception as e:
            logger.error(f"Error searching: {str(e)}")
            return []
    
    def extract_content_from_url(self, url: str, max_length: int = 2000) -> Optional[str]:
        """
        Extract text content from a URL.
        
        Args:
            url: URL to extract content from
            max_length: Maximum length of extracted content
        
        Returns:
            Extracted text content or None
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)
            
            # Limit length
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            return text
        
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {str(e)}")
            return None
    
    def search_and_extract(self, query: str, num_sources: int = 3) -> str:
        """
        Search and extract content from top results.
        
        Args:
            query: Search query
            num_sources: Number of sources to extract content from
        
        Returns:
            Combined context from search results
        """
        # Get search results
        search_results = self.search(query, max_results=num_sources)
        
        if not search_results:
            return "No search results found."
        
        # Extract content from top results
        contexts = []
        for i, result in enumerate(search_results[:num_sources]):
            url = result.get("url", "")
            snippet = result.get("snippet", "")
            
            # Try to get more content from URL
            if url:
                content = self.extract_content_from_url(url)
                if content:
                    contexts.append(f"Source {i+1} ({result.get('title', 'Unknown')}):\n{content}\n")
                elif snippet:
                    contexts.append(f"Source {i+1} ({result.get('title', 'Unknown')}):\n{snippet}\n")
            elif snippet:
                contexts.append(f"Source {i+1} ({result.get('title', 'Unknown')}):\n{snippet}\n")
        
        return "\n\n".join(contexts)

