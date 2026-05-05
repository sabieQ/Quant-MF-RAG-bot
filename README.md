# Quant Mutual Fund RAG Assistant

A complete Retrieval-Augmented Generation (RAG) system for answering factual FAQs about Quant Mutual Fund schemes. Built with a modular architecture, custom data pipelines, automated GitHub Action daily refreshes, and LLM failover strategies.

## Features
- **Facts-Only Guardrails**: Pre-processing classifiers and post-generation validators strictly enforce an advisory-free environment.
- **PII Redaction**: Blocks PAN, Aadhaar, Phone, and Emails.
- **Dual-LLM Engine**: Primary Groq (Llama-3) API with automatic fallback to Google Gemini Flash.
- **Automated Pipeline**: `scraper -> parser -> chunker -> vector indexer` pipeline automated via GitHub Actions for daily updates.
- **Streamlit UI**: Minimal, responsive chat interface with explicit citations and source links.

## Prerequisites
- Python 3.10+
- [Groq API Key](https://console.groq.com/)
- [Google Gemini API Key](https://aistudio.google.com/)

## Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd quant-mf-rag
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\Activate.ps1
   # Linux/Mac:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   Rename `.env.example` to `.env` and insert your API keys:
   ```env
   GROQ_API_KEY=your_groq_key
   GEMINI_API_KEY=your_gemini_key
   ```

## Running the Data Pipeline
To manually fetch the latest fund data and build the Vector DB:
```bash
python scripts/run_pipeline.py
```
*(Note: This is automatically handled by the `.github/workflows/daily-refresh.yml` action at midnight UTC).*

## Running the Assistant UI
```bash
streamlit run ui/app.py
```
The app will open at `http://localhost:8501`.

## Running Tests
```bash
pytest tests/ -v
```

## Architecture
See `phase-architecture.md` for the full technical specification.
