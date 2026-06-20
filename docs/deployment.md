# Deployment Guide

## Streamlit Community Cloud

MedIntel AI is designed to be easily deployed to Streamlit Community Cloud.

### Prerequisites
1. Push your repository to GitHub.
2. Ensure `requirements.txt` is up-to-date in the root directory.

### Steps
1. Log in to [Streamlit Community Cloud](https://share.streamlit.io/).
2. Click **New app**.
3. Select your repository, branch, and set the main file path to `app.py`.
4. Click **Advanced Settings** before deploying.
5. Add your environment variables to the Secrets section:
   ```toml
   GROQ_API_KEY = "your_key"
   SUPABASE_URL = "your_url"
   SUPABASE_ANON_KEY = "your_anon_key"
   ```
6. Click **Deploy**.

### Notes on Memory Limits
- Streamlit Cloud free tier has a ~1GB memory limit.
- The `sentence-transformers` model (`all-MiniLM-L6-v2`) and FAISS indices will consume memory. If you experience Out of Memory (OOM) errors, consider scaling to a paid tier or utilizing an external vector database (like Supabase Vector/pgvector) instead of local FAISS.
