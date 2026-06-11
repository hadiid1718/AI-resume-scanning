from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from frontend.components.alerts import show_error, show_success, show_warning
from frontend.components.charts import render_skills_chart
from frontend.components.loading import loading_context
from frontend.services.api_client import APIClient, APIError
from frontend.utils.session_state import init_session_state
from frontend.utils.styles import page_header


def _parse_job_locally(title: str, description: str) -> dict:
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from backend.app.modules.jd_parser import JDParser

    return JDParser().parse(title, description)


def render() -> None:
    init_session_state()
    page_header(
        "Job Description Upload",
        "Define the role requirements used for matching and ranking",
    )

    client = APIClient(st.session_state.backend_url)

    col1, col2 = st.columns([1, 2])
    with col1:
        job_title = st.text_input(
            "Job title",
            value=st.session_state.job_title,
            placeholder="e.g. Senior Python Developer",
        )
        st.session_state.job_title = job_title

    with col2:
        st.caption("This title is used across analysis, reports, and rankings.")

    job_description = st.text_area(
        "Job description",
        value=st.session_state.job_description,
        height=320,
        placeholder="Paste the full job description including requirements, skills, and responsibilities…",
        key="jd_text_area",
    )
    st.session_state.job_description = job_description

    col_parse, col_sample = st.columns(2)
    with col_parse:
        parse_clicked = st.button("Parse job description", type="primary", use_container_width=True)
    with col_sample:
        if st.button("Load sample JD", use_container_width=True):
            st.session_state.job_title = "Python Backend Engineer"
            st.session_state.job_description = (
                "We are seeking a Python Backend Engineer with 3+ years of experience.\n\n"
                "Requirements:\n"
                "- Strong Python, FastAPI, and REST API design\n"
                "- PostgreSQL and SQLAlchemy\n"
                "- Docker and CI/CD pipelines\n"
                "- Unit testing with pytest\n\n"
                "Nice to have:\n"
                "- AWS or cloud deployment\n"
                "- Redis caching\n"
                "- Machine learning basics"
            )
            st.rerun()

    if parse_clicked:
        if not job_description.strip():
            show_error("Job description text is required.")
        else:
            try:
                with loading_context("Parsing job description…"):
                    parsed = client.parse_job(job_title, job_description)
                st.session_state.parsed_job = parsed
                show_success("Job description parsed successfully.")
            except APIError:
                with loading_context("Parsing locally…"):
                    st.session_state.parsed_job = _parse_job_locally(job_title, job_description)
                show_warning("Backend unavailable — parsed using local engine.")

    parsed = st.session_state.parsed_job
    if parsed:
        st.markdown("### Parsed requirements")

        skills = parsed.get("skills") or parsed.get("required_skills", [])
        requirements = parsed.get("requirements", [])

        metric_cols = st.columns(3)
        metric_cols[0].metric("Skills detected", len(skills))
        metric_cols[1].metric("Requirements", len(requirements))
        metric_cols[2].metric(
            "Experience",
            parsed.get("experience_required") or "Not specified",
        )

        tab_skills, tab_reqs, tab_raw = st.tabs(["Skills", "Requirements", "Full JSON"])

        with tab_skills:
            if skills:
                st.markdown(" ".join(f"`{s}`" for s in skills))
            else:
                st.caption("No skills extracted.")

        with tab_reqs:
            if requirements:
                for req in requirements:
                    st.markdown(f"- {req}")
            else:
                st.caption("No structured requirements found.")

        with tab_raw:
            st.json(parsed)

        if skills:
            st.markdown("### Skill demand")
            render_skills_chart(skills[:10], [])

    elif not job_description.strip():
        show_warning("Enter a job description and click **Parse job description** to extract requirements.")
