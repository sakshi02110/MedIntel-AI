"""
Vector Store Service for MedIntel AI.

Manages FAISS indices for per-report and knowledge-base embeddings using LangChain.
"""

import os
from pathlib import Path
from typing import List, Optional

from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from src.services.embedding_service import EmbeddingService
from src.utils.logger import get_logger

logger = get_logger("medintel.vector_service")

VECTOR_DB_DIR = Path("data/vector_db")


class VectorService:
    """
    Manages building, saving, loading, and querying FAISS vector stores.
    """

    def __init__(self):
        VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
        self.embedding_service = EmbeddingService()
        logger.info("VectorService initialized.")

    def build_and_save_index(self, report_id: str, report_text: str) -> bool:
        """
        Chunks the report text, embeds it, and saves the FAISS index locally.
        """
        if not report_text.strip():
            logger.warning(f"Empty text provided for report_id: {report_id}")
            return False

        logger.info(f"Building index for report: {report_id}")
        
        # 1. Chunking
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        chunks = text_splitter.split_text(report_text)
        
        docs = [Document(page_content=chunk, metadata={"report_id": report_id}) for chunk in chunks]

        # 2. Embed and build FAISS index
        try:
            vectorstore = FAISS.from_documents(docs, self.embedding_service.get_embeddings_model())
            
            # 3. Save to disk
            index_path = VECTOR_DB_DIR / str(report_id)
            vectorstore.save_local(str(index_path))
            logger.info(f"Saved FAISS index to {index_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to build and save FAISS index for {report_id}: {e}")
            return False

    def load_index(self, report_id: str) -> Optional[FAISS]:
        """Loads a saved FAISS index from disk."""
        index_path = VECTOR_DB_DIR / str(report_id)
        if not index_path.exists():
            logger.warning(f"FAISS index not found at {index_path}")
            return None
        
        try:
            vectorstore = FAISS.load_local(
                str(index_path), 
                self.embedding_service.get_embeddings_model(),
                allow_dangerous_deserialization=True # required for local loading in new LangChain versions
            )
            return vectorstore
        except Exception as e:
            logger.error(f"Failed to load FAISS index for {report_id}: {e}")
            return None

    def search(self, vectorstore: FAISS, query: str, k: int = 4) -> List[Document]:
        """Perform similarity search on a loaded vectorstore."""
        try:
            return vectorstore.similarity_search(query, k=k)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
            
    def get_retriever(self, report_id: str):
        """Returns a LangChain retriever for the given report, if available."""
        vectorstore = self.load_index(report_id)
        if vectorstore:
            return vectorstore.as_retriever(search_kwargs={"k": 4})
        return None
