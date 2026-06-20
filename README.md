# MedIntel AI 🏥

> **Production-grade Multi-Agent Medical Report Intelligence System**

MedIntel AI analyzes medical lab reports using Groq's Llama 3.3 70B, LangChain RAG, and Supabase — giving patients clear, actionable insights from their blood work.

---

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
| LLM | Groq – Llama 3.3 70B |
| RAG | LangChain + FAISS |
| Embeddings | all-MiniLM-L6-v2 |
| Database | Supabase PostgreSQL |
| Auth | Supabase Auth |
| PDF | pdfplumber |
| Charts | Plotly + Matplotlib |

---

*Built with ❤️ using MedIntel AI*
