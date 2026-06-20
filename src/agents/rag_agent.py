"""
RAG Chat Agent for MedIntel AI.

Implements conversational question-answering over uploaded medical reports
using LangChain, FAISS, HuggingFace embeddings, and Groq Llama 3.3 70B.
"""

from typing import List, Dict, Any, Optional

from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage

from src.services.vector_service import VectorService
from src.utils.logger import get_logger
import os
from dotenv import load_dotenv

load_dotenv()
logger = get_logger("medintel.rag_agent")

# ── Prompts ───────────────────────────────────────────────────────────────────

# Contextualize question prompt (for handling follow-ups)
contextualize_q_system_prompt = """Given a chat history and the latest user question \
which might reference context in the chat history, formulate a standalone question \
which can be understood without the chat history. Do NOT answer the question, \
just reformulate it if needed and otherwise return it as is."""

contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

# QA System prompt
qa_system_prompt = """You are MedIntel AI, a medical assistant. \
Use the following pieces of retrieved context from the patient's lab report to answer the question. \
If you don't know the answer or the context doesn't contain the answer, say that you don't know based on the report. \
Do not make up values. Use clear, patient-friendly language. \
Remember that you are providing information, not diagnosing or treating. \
Context: {context}"""

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)


class RAGChatAgent:
    """
    RAG Agent using LangChain for Q&A over medical reports.
    """

    def __init__(self, vector_service: Optional[VectorService] = None):
        self.vector_service = vector_service or VectorService()
        api_key = os.getenv("GROQ_API_KEY")
        
        if not api_key:
            logger.error("GROQ_API_KEY missing. RAGChatAgent will fail.")
        
        self.llm = ChatGroq(
            groq_api_key=api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=1024
        )
        logger.info("RAGChatAgent initialized.")

    def ensure_index_exists(self, report_id: str, report_text: str) -> bool:
        """Build FAISS index if it doesn't exist."""
        if not self.vector_service.load_index(report_id):
            logger.info(f"Building missing FAISS index for report {report_id}...")
            return self.vector_service.build_and_save_index(report_id, report_text)
        return True

    def chat(self, report_id: str, query: str, chat_history: List[Dict[str, str]]) -> str:
        """
        Processes a user query given the report_id and conversation history.
        """
        logger.info(f"RAG chat query for report {report_id}: {query}")
        
        retriever = self.vector_service.get_retriever(report_id)
        if not retriever:
            return "I'm sorry, but I couldn't access the text for this report. Please ensure the report was uploaded correctly."

        # Convert simple dict history to LangChain message objects
        lc_history = []
        for msg in chat_history:
            if msg["role"] == "user":
                lc_history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_history.append(AIMessage(content=msg["content"]))

        # Build chains
        history_aware_retriever = create_history_aware_retriever(
            self.llm, retriever, contextualize_q_prompt
        )
        
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        
        # Invoke chain
        try:
            response = rag_chain.invoke({"input": query, "chat_history": lc_history})
            return response["answer"]
        except Exception as e:
            logger.error(f"RAG chain failed: {e}", exc_info=True)
            return "An error occurred while generating the answer. Please try again."
