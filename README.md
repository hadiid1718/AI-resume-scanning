# AI Resume Scanning System

This workspace is scaffolded around the requested architecture:

- Streamlit frontend
- FastAPI backend services
- PostgreSQL persistence
- Modular stages for upload, parsing, extraction, matching, ranking, AI evaluation, and reporting

## Structure

```text
backend/
  app/
    api/
    core/
    db/
    modules/
    schemas/
    services/
frontend/
docker-compose.yml
requirements.txt
```

## Quick Start

1. Copy `.env.example` to `.env` and adjust values if needed.
2. Start PostgreSQL:

```bash
docker compose up -d postgres
```

1. Run the backend API:

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

1. Run the Streamlit app:

```bash
streamlit run frontend/streamlit_app.py
```

## Notes

- The parser is scaffolded for a text-first workflow with room to add stronger PDF/DOCX parsing.
- The AI evaluation engine is provider-agnostic so you can plug in OpenAI or another LLM later.
- The frontend falls back to the local pipeline if the backend API is unavailable.
