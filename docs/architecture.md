# MedIntel AI Architecture

## Overview
MedIntel AI is a Streamlit-based application designed to analyze medical reports and provide patient-friendly insights using Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG).

## Components
1. **Frontend (Streamlit)**: Provides a responsive, interactive UI.
2. **Backend Services**:
   - `PDFService`: Validates and extracts text/tables from PDFs.
   - `LLMService`: Interfaces with Groq API for LLM completion with exponential backoff.
   - `EmbeddingService`: Manages HuggingFace embeddings (`all-MiniLM-L6-v2`).
   - `VectorService`: Handles document chunking and FAISS indexing.
3. **Agent Layer**:
   - `ReportTypeDetectionAgent`: Classifies report types.
   - `MedicalAnalysisAgent`: Extracts structured biomarkers.
   - `RAGChatAgent`: Answers questions over report context.
   - `TrendAnalysisAgent`: Computes cross-report trends.
   - `DoctorPrepAgent`: Generates questions for physician visits.
   - `RiskAssessmentAgent`: Evaluates risk across health categories.
4. **Database (Supabase PostgreSQL)**: Stores users, sessions, chat history, and report data.

## Data Flow
- User uploads PDF -> Validated -> Parsed by `pdfplumber` -> Classified by Type Agent -> Analysed by Analysis Agent -> Results stored in Supabase -> Vector index created by FAISS.
- For chat: User queries -> RAG Agent searches FAISS -> Constructs prompt -> Groq LLM -> Response sent to UI & stored in DB.
