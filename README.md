# MedIntel AI 🏥

> **Production-grade Multi-Agent Medical Report Intelligence System**


AI-Powered Medical Report Intelligence System

MedIntel AI is a production-grade multi-agent healthcare intelligence platform that transforms complex medical lab reports into clear, actionable insights. Using Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), vector search, and medical analytics, the system helps patients better understand their health reports and prepare for informed discussions with healthcare professionals.

The platform supports multiple report types including CBC, Lipid Profile, Thyroid Reports, Vitamin Reports, Blood Sugar Reports, Liver Function Tests (LFT), and Kidney Function Tests (KFT).

MedIntel AI analyzes medical lab reports using Groq's Llama 3.3 70B, LangChain RAG, and Supabase — giving patients clear, actionable insights from their blood work.
---

✨ Key Features
📄 Smart Medical Report Analysis
Upload medical reports in PDF format
Automatic report validation and text extraction
AI-powered biomarker identification and interpretation
Plain-language explanations for non-technical users
Detection of abnormal and critical health parameters
🧠 Multi-Agent AI Architecture
🔍 Report Type Detection Agent

Automatically identifies report categories such as:

CBC (Complete Blood Count)
Lipid Profile
Thyroid Profile
Vitamin Reports
Blood Sugar Reports
Liver Function Tests
Kidney Function Tests
🩺 Medical Analysis Agent
Extracts biomarkers and values
Identifies abnormal parameters
Generates medical summaries
Provides patient-friendly explanations
Highlights potential health concerns
💬 RAG-Powered Medical Chat
Ask questions directly about uploaded reports
Semantic search using FAISS Vector Database
Context-aware medical Q&A
Instant retrieval of report-specific information
📈 Trend Analysis Agent
Compare multiple reports over time
Visualize biomarker progression
Identify improving or worsening health trends
Interactive Plotly-based analytics dashboard
🧑‍⚕️ Doctor Preparation Agent
Generates personalized doctor consultation questions
Highlights important biomarkers to discuss
Helps patients prepare for medical appointments
⚠️ Risk Assessment Agent
Health risk scoring system
Detection of potentially concerning biomarkers
Visual risk assessment dashboard
Early warning indicators for health monitoring
📊 Interactive Dashboard
Health summary overview
Biomarker status visualization
Risk assessment gauges
Interactive charts and analytics
🔐 Secure Authentication & Storage
User authentication with Supabase Auth
Secure cloud-based report storage
Session management and chat history
Role-based access control with Row Level Security (RLS)
## 🚀 Quick Start

### 1. Clone & Enter the Project
```bash
cd "e:/New folder"
```

### 2. Create a Virtual Environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
# The .env file has been pre-configured with your credentials.
# Verify it exists:
cat .env
```

### 5. Run the App
```bash
streamlit run app.py
```

The app will open at **http://localhost:8501**

---

## 🧠 System Architecture

```
User Upload PDF
      │
      ▼
PDF Validation ──► Size ≤ 20 MB │ Pages ≤ 50 │ Valid PDF
      │
      ▼
Text Extraction (pdfplumber)
      │
      ▼
Report Type Detection Agent ──► CBC | Lipid | Thyroid | Vitamin | Sugar | LFT | KFT
      │
      ▼
Medical Analysis Agent (Groq Llama 3.3 70B)
      │
      ▼
Multi-Agent Responses
  ├── Agent 3: Recommendations
  ├── Agent 4: Trend Analysis
  ├── Agent 5: Doctor Prep Questions
  └── Agent 6: Risk Assessment
      │
      ▼
Supabase Storage + FAISS Vector DB
      │
      ▼
Streamlit Dashboard
```

---

## 📁 Project Structure

```
├── app.py                      # Streamlit entry point
├── requirements.txt
├── .env                        # Your API keys (gitignored)
├── .env.example                # Template
├── .streamlit/config.toml      # Theme & server config
│
├── src/
│   ├── agents/
│   │   ├── type_detection_agent.py   # Report type classifier
│   │   ├── analysis_agent.py         # Medical analysis (Agent 1)
│   │   ├── rag_agent.py              # RAG Q&A (Agent 2)
│   │   ├── recommendation_agent.py   # Lifestyle recs (Agent 3)
│   │   ├── trend_agent.py            # Trend comparison (Agent 4)
│   │   ├── doctor_agent.py           # Visit prep (Agent 5)
│   │   └── risk_agent.py             # Risk scoring (Agent 6)
│   ├── services/
│   │   ├── pdf_service.py            # PDF extraction
│   │   ├── llm_service.py            # Groq API wrapper
│   │   ├── embedding_service.py      # HuggingFace embeddings
│   │   └── vector_service.py         # FAISS operations
│   ├── database/
│   │   └── supabase_client.py        # Supabase client
│   ├── ui/
│   │   ├── upload_page.py            # Upload & Analyze
│   │   ├── chat_page.py              # RAG Chat
│   │   ├── trends_page.py            # Trend Graphs
│   │   ├── doctor_page.py            # Doctor Questions
│   │   ├── dashboard.py              # Health Dashboard
│   │   └── settings_page.py          # Account Settings
│   ├── prompts/
│   │   ├── analysis_prompt.py
│   │   ├── recommendation_prompt.py
│   │   ├── doctor_prompt.py
│   │   └── risk_prompt.py
│   └── utils/
│       ├── logger.py
│       ├── validators.py
│       └── helpers.py
│
├── docs/
│   ├── architecture.md
│   ├── database.md
│   └── deployment.md
│
├── tests/
│   ├── test_pdf_service.py
│   ├── test_analysis_agent.py
│   └── test_type_detection.py
│
└── data/
    ├── reports/                  # Temp PDF storage
    └── vector_db/                # FAISS indices
```

---

## 🤖 Agents

| Agent | Purpose | Status |
|-------|---------|--------|
| **Type Detection** | Classify report type (CBC, Lipid, etc.) | ✅ Milestone 1 |
| **Analysis** | Extract & explain biomarkers | ✅ Milestone 1 |
| **RAG Chat** | Conversational Q&A over report | 🔜 Milestone 2 |
| **Recommendations** | Diet & lifestyle advice | 🔜 Milestone 5 |
| **Trend Analysis** | Multi-report comparison charts | 🔜 Milestone 5 |
| **Doctor Prep** | Consultation questions | 🔜 Milestone 6 |
| **Risk Assessment** | Heart/diabetes/vitamin risk scores | 🔜 Milestone 7 |

---

## 🔑 Required API Keys

| Service | Variable | Get it at |
|---------|----------|-----------|
| Groq | `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) |
| Supabase URL | `SUPABASE_URL` | [supabase.com](https://supabase.com) |
| Supabase Key | `SUPABASE_ANON_KEY` | Project → Settings → API |

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 📦 Supported Report Types

- ✅ Complete Blood Count (CBC)
- ✅ Lipid Profile
- ✅ Thyroid Profile (TSH, T3, T4)
- ✅ Vitamin Reports (D, B12, Folate)
- ✅ Blood Sugar Reports (FBS, HbA1c)
- ✅ Liver Function Test (LFT)
- ✅ Kidney Function Test (KFT)

---

## ⚠️ Disclaimer

MedIntel AI provides **educational information only**. It does **not** diagnose, treat, or prescribe. Always consult a qualified healthcare professional for medical advice.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit 1.32 |
| Backend  | Python
| LLM | Groq – Llama 3.3 70B |
| RAG | LangChain + FAISS |
| Embeddings | all-MiniLM-L6-v2 |
| Database | Supabase PostgreSQL |
| Auth | Supabase Auth |
| PDF | pdfplumber |
| Charts | Plotly + Matplotlib |

---
⚠️ Medical Disclaimer

MedIntel AI is intended for educational and informational purposes only. The platform does not diagnose, prescribe treatments, or replace professional medical advice. Always consult a qualified healthcare professional regarding medical decisions.

*Built with ❤️ using MedIntel AI*
