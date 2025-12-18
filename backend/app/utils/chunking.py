"""Text chunking utilities for document processing."""
from typing import List
import re


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[dict]:
    """
    Split text into chunks with overlap.
    
    Args:
        text: Text to chunk
        chunk_size: Maximum size of each chunk in characters
        overlap: Number of characters to overlap between chunks
    
    Returns:
        List of chunk dictionaries with content and metadata
    """
    if not text or len(text.strip()) == 0:
        return []
    
    chunks = []
    start = 0
    chunk_index = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundaries
        if end < len(text):
            # Look for sentence endings near the chunk boundary
            sentence_endings = ['. ', '.\n', '! ', '!\n', '? ', '?\n']
            best_break = end
            
            for ending in sentence_endings:
                # Check within last 200 chars of chunk
                search_start = max(start, end - 200)
                pos = text.rfind(ending, search_start, end)
                if pos != -1:
                    best_break = pos + len(ending)
                    break
            
            # If no sentence boundary found, try paragraph break
            if best_break == end:
                para_break = text.rfind('\n\n', search_start, end)
                if para_break != -1:
                    best_break = para_break + 2
            
            end = best_break
        
        chunk_text = text[start:end].strip()
        
        if chunk_text:
            chunks.append({
                "content": chunk_text,
                "chunk_index": chunk_index,
                "start_char": start,
                "end_char": end,
                "metadata": {}
            })
            chunk_index += 1
        
        # Move start position with overlap
        start = max(start + 1, end - overlap)
    
    return chunks


def chunk_by_paragraphs(text: str, max_chunk_size: int = 1000) -> List[dict]:
    """
    Chunk text by paragraphs, respecting max_chunk_size.
    
    Args:
        text: Text to chunk
        max_chunk_size: Maximum size of each chunk
    
    Returns:
        List of chunk dictionaries
    """
    if not text or len(text.strip()) == 0:
        return []
    
    # Split by double newlines (paragraphs)
    paragraphs = re.split(r'\n\s*\n', text)
    
    chunks = []
    current_chunk = ""
    chunk_index = 0
    start_char = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # If adding this paragraph would exceed max size, save current chunk
        if current_chunk and len(current_chunk) + len(para) + 2 > max_chunk_size:
            chunks.append({
                "content": current_chunk.strip(),
                "chunk_index": chunk_index,
                "start_char": start_char,
                "end_char": start_char + len(current_chunk),
                "metadata": {"type": "paragraph"}
            })
            start_char += len(current_chunk)
            current_chunk = para
            chunk_index += 1
        else:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
    
    # Add final chunk
    if current_chunk:
        chunks.append({
            "content": current_chunk.strip(),
            "chunk_index": chunk_index,
            "start_char": start_char,
            "end_char": start_char + len(current_chunk),
            "metadata": {"type": "paragraph"}
        })
    
    return chunks

