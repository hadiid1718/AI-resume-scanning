from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from frontend.components.alerts import show_error, show_success, show_warning
from frontend.components.file_upload import resume_uploader
from frontend.components.loading import loading_context
from frontend.services.api_client import APIClient, APIError
from frontend.utils.file_extract import FileExtractionError, extract_text_from_bytes
from frontend.utils.session_state import add_candidate, init_session_state, set_error
from frontend.utils.styles import page_header


def _run_local_analysis(resume_text: str, job_title: str, job_description: str) -> dict:
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from backend.app.services.pipeline import ResumeAnalysisPipeline

    pipeline = ResumeAnalysisPipeline()
    return pipeline.analyze(
        resume_text=resume_text,
        job_title=job_title,
        job_description=job_description,
    )


def render() -> None:
    init_session_state()
    page_header(
        "Resume Upload",
        "Upload single or multiple resumes for LangGraph + Gemini screening",
    )

    client = APIClient(st.session_state.backend_url)

    tab_upload, tab_paste = st.tabs(["File upload", "Paste text"])

    with tab_upload:
        uploaded_files = resume_uploader(key="resume_page_uploader", multiple=True)
        if uploaded_files:
            texts: list[str] = []
            try:
                progress = st.progress(0, text="Extracting text from files...")
                for idx, (uploaded_file, file_bytes) in enumerate(uploaded_files):
                    text = extract_text_from_bytes(uploaded_file.name, file_bytes)
                    texts.append(text)
                    progress.progress((idx + 1) / len(uploaded_files), text=f"Extracted {uploaded_file.name}")
                st.session_state.batch_resume_texts = texts
                if len(texts) == 1:
                    st.session_state.resume_text = texts[0]
                show_success(f"Loaded {len(texts)} resume(s).")
            except FileExtractionError as exc:
                show_error(str(exc))

            if st.button("Run batch analysis", type="primary", disabled=not st.session_state.job_description.strip()):
                if not st.session_state.job_description.strip():
                    show_error("Configure job description first.")
                else:
                    st.session_state.analysis_in_progress = True
                    status = st.status("Running LangGraph screening pipeline...", expanded=True)
                    try:
                        with loading_context("Analyzing resumes..."):
                            batch = client.analyze_batch(
                                texts,
                                st.session_state.job_title,
                                st.session_state.job_description,
                            )
                        for result in batch.get("results", []):
                            add_candidate(result)
                        status.update(label=f"Completed {len(batch.get('results', []))} analyses", state="complete")
                        show_success("Batch analysis complete.")
                    except APIError:
                        for text in texts:
                            result = _run_local_analysis(
                                text,
                                st.session_state.job_title,
                                st.session_state.job_description,
                            )
                            add_candidate(result)
                        status.update(label="Completed using local pipeline", state="complete")
                        show_warning("Backend unavailable — used local LangGraph pipeline.")
                    finally:
                        st.session_state.analysis_in_progress = False

    with tab_paste:
        pasted = st.text_area(
            "Resume text",
            value=st.session_state.resume_text,
            height=280,
            placeholder="Paste resume content here…",
            key="resume_paste_area",
        )
        if pasted != st.session_state.resume_text:
            st.session_state.resume_text = pasted

    if st.session_state.get("analysis_in_progress"):
        st.info("Processing resumes — LangGraph workflow in progress…")

    if st.session_state.resume_text.strip():
        st.markdown("### Single resume actions")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Parse resume", use_container_width=True):
                try:
                    with loading_context("Parsing..."):
                        st.session_state.parsed_resume = client.parse_resume(st.session_state.resume_text)
                    show_success("Resume parsed.")
                except APIError as exc:
                    show_error(str(exc))
        with col2:
            if st.button("Analyze against current job", type="primary", use_container_width=True):
                if not st.session_state.job_description.strip():
                    show_error("Job description required.")
                else:
                    try:
                        with loading_context("Analyzing..."):
                            result = client.analyze(
                                st.session_state.resume_text,
                                st.session_state.job_title,
                                st.session_state.job_description,
                            )
                    except APIError:
                        result = _run_local_analysis(
                            st.session_state.resume_text,
                            st.session_state.job_title,
                            st.session_state.job_description,
                        )
                    add_candidate(result)
                    show_success("Analysis complete.")
