from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from frontend.components.alerts import show_info, show_warning
from frontend.components.charts import render_match_breakdown, render_score_gauge, render_skills_chart
from frontend.components.metrics_cards import metric_row, recommendation_badge
from frontend.utils.scoring import extract_ai_score
from frontend.utils.session_state import get_candidates, get_selected_analysis, init_session_state, select_candidate
from frontend.utils.styles import page_header


def render() -> None:
    init_session_state()
    page_header("Candidate Details", "Structured profile, AI score, skills, and evaluation")

    candidates = get_candidates()
    if not candidates:
        show_warning("No analyzed candidates yet.")
        show_info("Upload resumes and run batch analysis.")
        return

    names = [c["name"] for c in candidates]
    current_index = st.session_state.get("selected_candidate_index", 0)
    if current_index >= len(candidates):
        current_index = 0

    selected_name = st.selectbox("Select candidate", names, index=current_index, key="details_candidate_select")
    select_candidate(candidates[names.index(selected_name)]["id"])

    analysis = get_selected_analysis()
    if not analysis:
        show_warning("Could not load candidate analysis.")
        return

    candidate = analysis.get("candidate", {})
    job = analysis.get("job", {})
    match_result = analysis.get("match_result", {})
    evaluation = analysis.get("evaluation", {})
    ai_score = extract_ai_score(analysis)
    recommendation = analysis.get("recommendation", "Consider")

    metric_row(
        [
            ("AI Score", f"{ai_score}/100", None),
            ("Recommendation", recommendation, None),
            ("Skills Matched", str(len(match_result.get("overlap_skills", []))), None),
            ("Skill Gaps", str(len(match_result.get("missing_skills", []))), None),
        ]
    )

    col_gauge, col_summary = st.columns([1, 2])
    with col_gauge:
        render_score_gauge(ai_score, "AI Score")
    with col_summary:
        st.markdown("**Recommendation**")
        st.markdown(recommendation_badge(recommendation), unsafe_allow_html=True)
        st.markdown("**Summary**")
        st.write(evaluation.get("summary") or "—")
        st.markdown(f"**Role:** {job.get('title', st.session_state.job_title)}")

    tab_profile, tab_skills, tab_eval, tab_raw = st.tabs(
        ["Profile", "Skills & Match", "Evaluation", "Raw data"]
    )

    with tab_profile:
        profile_cols = st.columns(2)
        with profile_cols[0]:
            st.markdown("**Contact**")
            st.markdown(f"- **Name:** {candidate.get('full_name') or '—'}")
            st.markdown(f"- **Email:** {candidate.get('email') or '—'}")
            st.markdown(f"- **Phone:** {candidate.get('phone') or candidate.get('phone_number') or '—'}")
            st.markdown(f"- **Location:** {candidate.get('location') or '—'}")
        with profile_cols[1]:
            st.markdown("**Links**")
            st.markdown(f"- **LinkedIn:** {candidate.get('linkedin_url') or '—'}")
            st.markdown(f"- **GitHub:** {candidate.get('github_url') or '—'}")

        if candidate.get("education"):
            st.markdown("**Education**")
            for item in candidate.get("education", [])[:5]:
                st.markdown(f"- {item if isinstance(item, str) else item}")

        if candidate.get("certifications"):
            st.markdown("**Certifications**")
            for item in candidate.get("certifications", [])[:5]:
                st.markdown(f"- {item}")

        if candidate.get("projects"):
            st.markdown("**Projects**")
            for item in candidate.get("projects", [])[:5]:
                if isinstance(item, dict):
                    st.markdown(f"- **{item.get('name', 'Project')}:** {item.get('description', '')}")
                else:
                    st.markdown(f"- {item}")

        if candidate.get("work_experience") or candidate.get("work_history"):
            st.markdown("**Work Experience**")
            for item in (candidate.get("work_experience") or candidate.get("work_history"))[:5]:
                if isinstance(item, dict):
                    st.markdown(
                        f"- **{item.get('title', '')}** @ {item.get('company', '')} ({item.get('duration', '')})"
                    )
                    if item.get("summary"):
                        st.caption(item["summary"])

    with tab_skills:
        overlap = match_result.get("overlap_skills", [])
        missing = match_result.get("missing_skills", [])
        render_skills_chart(overlap, missing)
        render_match_breakdown(match_result)

    with tab_eval:
        eval_cols = st.columns(3)
        with eval_cols[0]:
            st.markdown("**Strengths**")
            for item in evaluation.get("strengths", []):
                st.markdown(f"- {item}")
        with eval_cols[1]:
            st.markdown("**Weaknesses**")
            for item in evaluation.get("weaknesses", evaluation.get("gaps", [])):
                st.markdown(f"- {item}")
        with eval_cols[2]:
            st.markdown("**Recommendations**")
            for item in evaluation.get("recommendations", []):
                st.markdown(f"- {item}")

        if evaluation.get("skills_analysis"):
            st.markdown("**Skills analysis**")
            st.write(evaluation["skills_analysis"])
        if evaluation.get("experience_analysis"):
            st.markdown("**Experience analysis**")
            st.write(evaluation["experience_analysis"])

    with tab_raw:
        st.json(analysis)
