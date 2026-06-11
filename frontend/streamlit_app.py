from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from frontend.components.sidebar import render_sidebar
from frontend.pages import (
    candidate_comparison,
    candidate_details,
    candidate_rankings,
    dashboard,
    job_description,
    reports_download,
    resume_upload,
)
from frontend.utils.config import APP_ICON, APP_TITLE
from frontend.utils.deps import ensure_analysis_deps
from frontend.utils.styles import inject_global_styles

PAGES = {
    "Dashboard": dashboard.render,
    "Resume Upload": resume_upload.render,
    "Job Description Upload": job_description.render,
    "Candidate Rankings": candidate_rankings.render,
    "Candidate Details": candidate_details.render,
    "Candidate Comparison": candidate_comparison.render,
    "Reports Download": reports_download.render,
}


def main() -> None:
    ensure_analysis_deps()
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_global_styles()

    page_names = list(PAGES.keys())
    selected = render_sidebar(page_names)
    if selected:
        PAGES[selected]()


if __name__ == "__main__":
    main()
