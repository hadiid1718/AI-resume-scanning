from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from frontend.components.alerts import show_info, show_warning
from frontend.components.charts import render_score_gauge
from frontend.components.metrics_cards import recommendation_badge
from frontend.utils.scoring import extract_ai_score
from frontend.utils.session_state import get_candidates, init_session_state
from frontend.utils.styles import page_header


def _render_panel(entry: dict) -> None:
    analysis = entry["analysis"]
    candidate = analysis.get("candidate", {})
    evaluation = analysis.get("evaluation") or {}
    ai_score = extract_ai_score(analysis)
    rec = entry.get("recommendation") or analysis.get("recommendation", "Consider")

    st.markdown(f"### {entry.get('name', 'Unknown')}")
    render_score_gauge(ai_score, "AI Score")
    st.markdown(recommendation_badge(rec), unsafe_allow_html=True)
    st.markdown(f"**Email:** {candidate.get('email') or '—'}")
    st.markdown(f"**Phone:** {candidate.get('phone') or candidate.get('phone_number') or '—'}")
    skills = candidate.get("skills") or []
    if skills:
        st.markdown("**Skills:** " + ", ".join(str(s) for s in skills[:10]))
    st.markdown("**Summary**")
    st.write(evaluation.get("summary") or candidate.get("summary") or "—")
    st.markdown("**Strengths**")
    for item in evaluation.get("strengths", [])[:5]:
        st.markdown(f"- {item}")
    st.markdown("**Weaknesses**")
    for item in evaluation.get("weaknesses", evaluation.get("gaps", []))[:5]:
        st.markdown(f"- {item}")


def render() -> None:
    init_session_state()
    page_header("Candidate Comparison", "Side-by-side comparison of two candidates")

    candidates = get_candidates()
    if len(candidates) < 2:
        show_warning("Need at least two analyzed candidates to compare.")
        show_info("Upload and analyze multiple resumes first.")
        return

    names = [c["name"] for c in candidates]
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        left_name = st.selectbox("Candidate A", names, index=0, key="compare_a")
    with col_sel2:
        right_default = 1 if len(names) > 1 else 0
        right_name = st.selectbox("Candidate B", names, index=right_default, key="compare_b")

    left = candidates[names.index(left_name)]
    right = candidates[names.index(right_name)]

    col1, col2 = st.columns(2)
    with col1:
        _render_panel(left)
    with col2:
        _render_panel(right)

    st.divider()
    left_score = extract_ai_score(left["analysis"])
    right_score = extract_ai_score(right["analysis"])
    if left_score > right_score:
        st.info(f"**{left_name}** leads by {left_score - right_score} points.")
    elif right_score > left_score:
        st.info(f"**{right_name}** leads by {right_score - left_score} points.")
    else:
        st.info("Both candidates have the same AI score.")
