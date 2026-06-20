"""
Embedding Service for MedIntel AI.

Uses HuggingFace sentence-transformers (all-MiniLM-L6-v2)
to generate dense vector embeddings for RAG.
"""

from typing import List
from langchain_community.embeddings import HuggingFaceEmbeddings
from src.utils.logger import get_logger

logger = get_logger("medintel.embedding_service")


class EmbeddingService:
    """
    Wrapper around HuggingFace embeddings.
    """
    
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        logger.info("Initializing HuggingFaceEmbeddings (all-MiniLM-L6-v2)...")
        # Initialize LangChain's HuggingFaceEmbeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},  # Can be changed to 'cuda' if GPU available
            encode_kwargs={'normalize_embeddings': True}
        )
        logger.info("Embedding model loaded.")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of documents."""
        return self.embeddings.embed_documents(texts)

    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a single query."""
        return self.embeddings.embed_query(query)
        
    def get_embeddings_model(self):
        """Return the LangChain embeddings object for use in FAISS."""
        return self.embeddings
