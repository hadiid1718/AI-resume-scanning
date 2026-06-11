import os
from pathlib import Path

DEFAULT_BACKEND_URL = "http://localhost:8000"
APP_TITLE = "AI Resume Scanning"
APP_ICON = ":material/analytics:"


def get_backend_url() -> str:
    return os.environ.get("STREAMLIT_BACKEND_URL", DEFAULT_BACKEND_URL).rstrip("/")


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]
