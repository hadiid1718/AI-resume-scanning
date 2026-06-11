"""Start the FastAPI backend. Run from the project root:

    python run_backend.py
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(ROOT / "backend")],
    )
