from pathlib import Path
import sys


def ensure_project_root() -> Path:
    """Add the repository root to sys.path so `frontend` and `backend` import correctly."""
    root = Path(__file__).resolve().parents[2]
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return root
