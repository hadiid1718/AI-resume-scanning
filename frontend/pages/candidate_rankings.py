from pathlib import Path
import sys

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from frontend.components.alerts import show_info, show_warning
from frontend.components.charts import render_ranking_bar_chart, render_score_gauge
from frontend.components.metrics_cards import recommendation_badge
from frontend.utils.scoring import extract_ai_score
from frontend.utils.session_state import get_candidates, init_session_state, select_candidate
from frontend.utils.styles import page_header


def _experience_summary(analysis: dict) -> str:
    evaluation = analysis.get("evaluation") or {}
    if evaluation.get("experience_analysis"):
        return str(evaluation["experience_analysis"])[:120]
    candidate = analysis.get("candidate") or {}
    work = candidate.get("work_experience") or candidate.get("work_history") or []
    if work and isinstance(work[0], dict):
        item = work[0]
        return f"{item.get('title', '')} @ {item.get('company', '')}".strip(" @")
    return "—"


def render() -> None:
    init_session_state()
    page_header("Candidate Rankings", "AI-scored candidates ranked highest to lowest")

    candidates = get_candidates()
    if not candidates:
        show_warning("No candidates yet. Upload resumes and run batch analysis.")
        show_info("Go to **Resume Upload** and run **Run batch analysis**.")
        return

    sorted_candidates = sorted(
        candidates,
        key=lambda c: extract_ai_score(c["analysis"]),
        reverse=True,
    )

    col_search, col_min, col_rec = st.columns([2, 1, 1])
    with col_search:
        search = st.text_input("Search by name or email", placeholder="Type to filter...")
    with col_min:
        min_score = st.slider("Minimum AI score", 0, 100, 0)
    with col_rec:
        rec_filter = st.selectbox(
            "Recommendation",
            ["All", "Highly Recommended", "Recommended", "Consider", "Not Recommended"],
        )

    filtered = []
    for entry in sorted_candidates:
        analysis = entry["analysis"]
        candidate = analysis.get("candidate", {})
        ai_score = extract_ai_score(analysis)
        recommendation = entry.get("recommendation") or analysis.get("recommendation", "Consider")
        name = entry.get("name", "")
        email = candidate.get("email") or ""
        haystack = f"{name} {email}".lower()
        if search and search.lower() not in haystack:
            continue
        if ai_score < min_score:
            continue
        if rec_filter != "All" and recommendation != rec_filter:
            continue
        filtered.append(entry)

    rows = []
    for rank_pos, entry in enumerate(filtered, start=1):
        analysis = entry["analysis"]
        candidate = analysis.get("candidate", {})
        ai_score = extract_ai_score(analysis)
        skills = candidate.get("skills") or []
        if isinstance(skills, dict):
            skills = list(skills.values())
        rows.append(
            {
                "Rank": rank_pos,
                "Candidate": entry.get("name", "Unknown"),
                "AI Score": ai_score,
                "Recommendation": entry.get("recommendation") or analysis.get("recommendation"),
                "Key Skills": ", ".join(str(s) for s in skills[:5]) or "—",
                "Experience": _experience_summary(analysis)[:60],
                "Email": candidate.get("email") or "—",
            }
        )

    if not rows:
        show_warning("No candidates match your filters.")
        return

    df = pd.DataFrame(rows)
    col_chart, col_table = st.columns([1, 1])
    with col_chart:
        st.markdown("### Score distribution")
        render_ranking_bar_chart(filtered, score_key="ai_score")
    with col_table:
        st.markdown("### Ranked candidates")
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "AI Score": st.column_config.ProgressColumn(
                    "AI Score",
                    format="%d",
                    min_value=0,
                    max_value=100,
                ),
            },
        )

    st.divider()
    names = [f"{i + 1}. {c['name']}" for i, c in enumerate(filtered)]
    selected_label = st.selectbox("Select candidate", names)
    selected_index = names.index(selected_label)
    entry = filtered[selected_index]

    col1, col2, col3 = st.columns(3)
    with col1:
        render_score_gauge(extract_ai_score(entry["analysis"]), "AI Score")
    with col2:
        rec = entry.get("recommendation") or entry["analysis"].get("recommendation", "Consider")
        st.markdown("**Recommendation**")
        st.markdown(recommendation_badge(rec), unsafe_allow_html=True)
    with col3:
        if st.button("View details", type="primary"):
            select_candidate(entry["id"])
            st.session_state["_navigate_to"] = "Candidate Details"
            st.rerun()
        if st.button("Compare candidates"):
            st.session_state["_navigate_to"] = "Candidate Comparison"
            st.rerun()
