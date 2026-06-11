from __future__ import annotations

import subprocess
import sys


def _install(package: str) -> None:
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", package, "-q"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def ensure_file_extraction_deps() -> None:
    """Install PDF/DOCX libraries into the active Python if missing."""
    try:
        import fitz  # noqa: F401
    except ModuleNotFoundError:
        _install("pymupdf")

    try:
        import docx  # noqa: F401
    except ModuleNotFoundError:
        _install("python-docx")


def ensure_analysis_deps() -> None:
    """Install dependencies needed for local pipeline fallback."""
    ensure_file_extraction_deps()
    try:
        import spacy  # noqa: F401
    except ModuleNotFoundError:
        _install("spacy")
