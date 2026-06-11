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
2. Install dependencies and register the project package:

```bash
pip install -r requirements.txt
pip install -e .
```

3. Start PostgreSQL (optional):

```bash
docker compose up -d postgres
```

4. Run the backend API:

```bash
# Recommended — works from project root OR backend/ folder
python backend/run.py
```

If you are already inside `backend/`:

```bash
python run.py
```

Do **not** use `uvicorn backend.app.main:app` from inside `backend/` — Python cannot find the `backend` package from that folder.

Alternative (project root only):

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Run the Streamlit frontend:

```bash
python frontend/run.py
```

Or from the project root:

```bash
streamlit run frontend/streamlit_app.py
```

Or use the helper script:

```bash
.\start-frontend.ps1
```

## Notes

- The parser is scaffolded for a text-first workflow with room to add stronger PDF/DOCX parsing.
- The AI evaluation engine is provider-agnostic so you can plug in OpenAI or another LLM later.
- The frontend falls back to the local pipeline if the backend API is unavailable.
