"""RAG (Retrieval-Augmented Generation) service."""
from typing import List, Dict, Optional
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG pipeline combining retrieval and generation."""
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        llm_service: LLMService
    ):
        """
        Initialize RAG service.
        
        Args:
            embedding_service: Embedding service instance
            llm_service: LLM service instance
        """
        self.embedding_service = embedding_service
        self.llm_service = llm_service
        logger.info("RAG service initialized")
    
    def answer_question(
        self,
        question: str,
        document_id: str,
        collection_name: Optional[str] = None,
        top_k: int = 5,
        min_similarity: float = 0.0
    ) -> Dict:
        """
        Answer a question using RAG pipeline.
        
        Args:
            question: User's question
            document_id: UUID of the document
            collection_name: Collection name (default: documents_{document_id})
            top_k: Number of chunks to retrieve
            min_similarity: Minimum similarity threshold
        
        Returns:
            Dictionary with answer and sources
        """
        try:
            # Determine collection name
            if not collection_name:
                collection_name = f"documents_{document_id}"
            
            # Retrieve relevant chunks
            similar_chunks = self.embedding_service.search_similar_chunks(
                collection_name=collection_name,
                query=question,
                n_results=top_k,
                filter_dict={"document_id": str(document_id)}
            )
            
            if not similar_chunks:
                return {
                    "answer": "I couldn't find relevant information in the document to answer this question.",
                    "sources": []
                }
            
            # Filter by similarity (distance is cosine distance, lower is better)
            # Convert distance to similarity (1 - distance)
            filtered_chunks = []
            for chunk in similar_chunks:
                distance = chunk.get("distance", 1.0)
                similarity = 1.0 - distance if distance is not None else 0.0
                
                if similarity >= min_similarity:
                    chunk["similarity"] = similarity
                    filtered_chunks.append(chunk)
            
            if not filtered_chunks:
                return {
                    "answer": "I couldn't find relevant information in the document to answer this question.",
                    "sources": []
                }
            
            # Build context from retrieved chunks
            context = self._build_context(filtered_chunks)
            
            # Generate answer using LLM
            answer = self.llm_service.generate_answer(
                question=question,
                context=context
            )
            
            # Format sources
            sources = [
                {
                    "chunk_id": chunk["chunk_id"],
                    "content": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"],
                    "similarity": chunk.get("similarity", 0.0),
                    "metadata": chunk.get("metadata", {})
                }
                for chunk in filtered_chunks
            ]
            
            return {
                "answer": answer,
                "sources": sources
            }
        
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {str(e)}")
            raise
    
    def summarize_document(
        self,
        document_id: str,
        collection_name: Optional[str] = None,
        max_chunks: int = 50,
        db: Optional[Session] = None
    ) -> Dict:
        """
        Summarize a document by retrieving all chunks and generating a summary.
        
        Args:
            document_id: UUID of the document
            collection_name: Collection name (default: documents_{document_id})
            max_chunks: Maximum number of chunks to include in summary
        
        Returns:
            Dictionary with summary and sources
        """
        try:
            # Determine collection name
            if not collection_name:
                collection_name = f"documents_{document_id}"
            
            # Try to get all chunks from vector DB first
            all_chunks = []
            try:
                all_chunks = self.embedding_service.get_all_chunks(
                    collection_name=collection_name,
                    document_id=str(document_id),
                    limit=max_chunks
                )
            except Exception as e:
                logger.warning(f"Could not get chunks from vector DB: {str(e)}, trying database fallback")
            
            # Fallback to database if vector DB doesn't have chunks
            if not all_chunks and db:
                try:
                    from app.models.database import DocumentChunk
                    import uuid
                    doc_uuid = uuid.UUID(document_id)
                    db_chunks = db.query(DocumentChunk).filter(
                        DocumentChunk.document_id == doc_uuid
                    ).order_by(DocumentChunk.chunk_index).limit(max_chunks).all()
                    
                    all_chunks = [
                        {
                            "chunk_id": str(chunk.id),
                            "content": chunk.content,
                            "metadata": {
                                "chunk_index": chunk.chunk_index,
                                "document_id": str(chunk.document_id)
                            }
                        }
                        for chunk in db_chunks
                    ]
                    logger.info(f"Retrieved {len(all_chunks)} chunks from database as fallback")
                except Exception as e:
                    logger.error(f"Error getting chunks from database: {str(e)}")
            
            if not all_chunks:
                return {
                    "answer": "I couldn't find any content in the document to summarize. The document may not have been processed yet or there was an error during processing.",
                    "sources": []
                }
            
            # Build context from all chunks
            context = self._build_context(all_chunks)
            
            # Generate summary using LLM
            summary_prompt = f"""Please provide a comprehensive summary of the following document content. 
Include the main topics, key points, and important details. Be thorough but concise.

Document Content:
{context}

Summary:"""
            
            summary = self.llm_service.generate_answer(
                question=summary_prompt,
                context=None,
                system_prompt="You are an expert at summarizing documents. Provide clear, comprehensive summaries that capture the main ideas and key details."
            )
            
            # Format sources (show we used all chunks)
            sources = [
                {
                    "chunk_id": chunk.get("chunk_id", ""),
                    "content": chunk.get("content", "")[:200] + "..." if len(chunk.get("content", "")) > 200 else chunk.get("content", ""),
                    "metadata": chunk.get("metadata", {})
                }
                for chunk in all_chunks[:10]  # Show first 10 chunks as sources
            ]
            
            return {
                "answer": summary,
                "sources": sources
            }
        
        except Exception as e:
            logger.error(f"Error summarizing document: {str(e)}")
            raise
    
    def _build_context(self, chunks: List[Dict]) -> str:
        """Build context string from retrieved chunks."""
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            content = chunk.get("content", "")
            metadata = chunk.get("metadata", {})
            chunk_index = metadata.get("chunk_index", i)
            
            context_parts.append(f"[Section {chunk_index}]\n{content}\n")
        
        return "\n".join(context_parts)


