from pathlib import Path
import sys

import requests
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.services.pipeline import ResumeAnalysisPipeline  # noqa: E402


st.set_page_config(page_title="AI Resume Scanning System", page_icon="🧭", layout="wide")


def call_backend(backend_url: str, resume_text: str, job_title: str, job_description: str) -> dict | None:
    try:
        response = requests.post(
            f"{backend_url.rstrip('/')}/api/v1/analyze",
            data={"resume_text": resume_text, "job_title": job_title, "job_description": job_description},
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


def run_local_pipeline(resume_text: str, job_title: str, job_description: str) -> dict:
    pipeline = ResumeAnalysisPipeline()
    return pipeline.analyze(resume_text=resume_text, job_title=job_title, job_description=job_description)


st.title("AI Resume Scanning System")
st.caption("Upload or paste a resume, then compare it against a job description through the scanning pipeline.")

with st.sidebar:
    st.header("Analysis Controls")
    job_title = st.text_input("Job title", value="Python Backend Engineer")
    backend_url = st.text_input("Backend API", value="http://localhost:8000")
    st.info("If the backend is unavailable, the app will use the local pipeline fallback.")

left, right = st.columns(2)

with left:
    resume_text = st.text_area(
        "Resume text",
        height=320,
        placeholder="Paste the resume text here. PDF/DOCX parsing can be added into the parser module next.",
    )
    uploaded_file = st.file_uploader("Optional text resume upload", type=["txt", "md"])
    if uploaded_file is not None:
        try:
            resume_text = uploaded_file.read().decode("utf-8")
            st.success(f"Loaded {uploaded_file.name}")
        except Exception:
            st.warning("The uploaded file could not be read as UTF-8 text. Paste text manually for now.")

with right:
    job_description = st.text_area(
        "Job description",
        height=320,
        placeholder="Paste the job description here.",
    )

analyze_clicked = st.button("Run analysis", type="primary")

if analyze_clicked:
    if not resume_text.strip() or not job_description.strip():
        st.error("Provide both resume text and job description.")
    else:
        result = call_backend(backend_url, resume_text, job_title, job_description)
        if result is None:
            result = run_local_pipeline(resume_text, job_title, job_description)

        st.subheader("Result Summary")
        columns = st.columns(4)
        columns[0].metric("Match Score", f"{result['match_result']['score']:.2f}")
        columns[1].metric("Rank", result["rank_result"]["rank"].title())
        columns[2].metric("Assessment", result["evaluation"]["overall_assessment"].replace("_", " ").title())
        columns[3].metric("Skills Matched", len(result["match_result"].get("overlap_skills", [])))

        st.write("### Candidate")
        st.json(result["candidate"])

        st.write("### Job")
        st.json(result["job"])

        st.write("### Match")
        st.json(result["match_result"])

        st.write("### AI Evaluation")
        st.json(result["evaluation"])

        st.write("### Generated Report")
        st.code(result["report"]["markdown"], language="markdown")
