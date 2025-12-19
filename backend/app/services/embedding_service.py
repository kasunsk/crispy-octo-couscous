"""Embedding service for generating text embeddings."""
from typing import List, Optional
import chromadb
from chromadb.config import Settings
import os
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings and managing vector database."""
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        chroma_host: Optional[str] = None,
        chroma_port: Optional[int] = None
    ):
        """
        Initialize embedding service.
        
        Args:
            model_name: Name of the embedding model
            chroma_host: ChromaDB host (None for local)
            chroma_port: ChromaDB port (None for local)
        """
        self.model_name = model_name
        logger.info(f"Loading embedding model: {model_name}")
        
        # Load embedding model
        self.embedding_model = SentenceTransformer(model_name)
        
        # Initialize ChromaDB client
        if chroma_host and chroma_port:
            self.chroma_client = chromadb.HttpClient(
                host=chroma_host,
                port=chroma_port
            )
        else:
            # Local ChromaDB
            chroma_path = os.getenv("CHROMA_PATH", "./chroma_db")
            os.makedirs(chroma_path, exist_ok=True)
            
            self.chroma_client = chromadb.PersistentClient(
                path=chroma_path,
                settings=Settings(anonymized_telemetry=False)
            )
        
        logger.info("Embedding service initialized")
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings
        
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        try:
            embeddings = self.embedding_model.encode(
                texts,
                show_progress_bar=len(texts) > 10,
                convert_to_numpy=True
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    def get_or_create_collection(self, collection_name: str):
        """Get or create a ChromaDB collection."""
        try:
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            return collection
        except Exception as e:
            logger.error(f"Error getting/creating collection: {str(e)}")
            raise
    
    def add_document_chunks(
        self,
        collection_name: str,
        chunks: List[dict],
        document_id: str,
        filename: str,
        file_type: str
    ):
        """
        Add document chunks to vector database.
        
        Args:
            collection_name: Name of the collection
            chunks: List of chunk dictionaries with 'content' key
            document_id: UUID of the document
            filename: Original filename
            file_type: File type
        """
        if not chunks:
            return
        
        try:
            collection = self.get_or_create_collection(collection_name)
            
            # Extract texts
            texts = [chunk["content"] for chunk in chunks]
            
            # Generate embeddings
            embeddings = self.generate_embeddings(texts)
            
            # Prepare IDs and metadata
            ids = [f"{document_id}_{chunk['chunk_index']}" for chunk in chunks]
            metadatas = [
                {
                    "document_id": str(document_id),
                    "chunk_index": chunk["chunk_index"],
                    "filename": filename,
                    "file_type": file_type,
                    **chunk.get("metadata", {})
                }
                for chunk in chunks
            ]
            
            # Add to collection
            collection.add(
                embeddings=embeddings,
                documents=texts,
                ids=ids,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(chunks)} chunks to collection {collection_name}")
        
        except Exception as e:
            logger.error(f"Error adding chunks to vector DB: {str(e)}")
            raise
    
    def search_similar_chunks(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5,
        filter_dict: Optional[dict] = None
    ) -> List[dict]:
        """
        Search for similar chunks in vector database.
        
        Args:
            collection_name: Name of the collection
            query: Search query text
            n_results: Number of results to return
            filter_dict: Optional filter dictionary
        
        Returns:
            List of similar chunks with metadata
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            
            # Generate query embedding
            query_embedding = self.generate_embeddings([query])[0]
            
            # Search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_dict if filter_dict else None
            )
            
            # Format results
            similar_chunks = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    similar_chunks.append({
                        "chunk_id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if "distances" in results else None
                    })
            
            return similar_chunks
        
        except Exception as e:
            logger.error(f"Error searching similar chunks: {str(e)}")
            raise
    
    def get_all_chunks(
        self,
        collection_name: str,
        document_id: str,
        limit: int = 50
    ) -> List[dict]:
        """
        Get all chunks for a document from vector database.
        
        Args:
            collection_name: Name of the collection
            document_id: UUID of the document
            limit: Maximum number of chunks to return
        
        Returns:
            List of chunks with metadata
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            
            # Get all chunks for this document
            results = collection.get(
                where={"document_id": str(document_id)},
                limit=limit
            )
            
            # Format results
            chunks = []
            if results["ids"] and len(results["ids"]) > 0:
                for i in range(len(results["ids"])):
                    chunks.append({
                        "chunk_id": results["ids"][i],
                        "content": results["documents"][i],
                        "metadata": results["metadatas"][i] if results["metadatas"] else {}
                    })
            
            # Sort by chunk_index if available
            try:
                chunks.sort(key=lambda x: x.get("metadata", {}).get("chunk_index", 0))
            except:
                pass
            
            return chunks
        
        except Exception as e:
            logger.error(f"Error getting all chunks: {str(e)}")
            raise
    
    def delete_document(self, collection_name: str, document_id: str):
        """Delete all chunks for a document from vector database."""
        try:
            collection = self.get_or_create_collection(collection_name)
            collection.delete(where={"document_id": str(document_id)})
            logger.info(f"Deleted document {document_id} from collection {collection_name}")
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise


