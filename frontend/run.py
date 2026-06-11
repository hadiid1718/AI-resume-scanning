"""Run the Streamlit frontend from any directory.

From project root:
    python frontend/run.py

From frontend/ folder:
    python run.py
"""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit.web.cli as stcli

if __name__ == "__main__":
    app_path = PROJECT_ROOT / "frontend" / "streamlit_app.py"
    sys.argv = ["streamlit", "run", str(app_path)]
    sys.exit(stcli.main())
