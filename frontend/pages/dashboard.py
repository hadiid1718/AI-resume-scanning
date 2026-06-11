from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from frontend.components.alerts import show_info, show_warning
from frontend.components.charts import render_ranking_bar_chart, render_score_gauge
from frontend.components.metrics_cards import metric_row, recommendation_badge
from frontend.services.api_client import APIClient, APIError
from frontend.utils.scoring import extract_ai_score
from frontend.utils.session_state import get_candidates, init_session_state
from frontend.utils.styles import page_header


def render() -> None:
    init_session_state()
    page_header("Dashboard", "AI resume screening overview")

    candidates = get_candidates()
    client = APIClient(st.session_state.backend_url)

    if st.button("Load rankings from database"):
        try:
            data = client.get_rankings()
            for row in data.get("rankings", []):
                payload = row.get("payload")
                if payload:
                    from frontend.utils.session_state import add_candidate

                    add_candidate(payload)
            show_info(f"Loaded {data.get('total', 0)} candidates from database.")
        except APIError as exc:
            show_warning(str(exc))

    if candidates:
        scores = [extract_ai_score(c["analysis"]) for c in candidates]
        avg_score = sum(scores) / len(scores) if scores else 0
        best = max(scores) if scores else 0
        highly = sum(1 for c in candidates if c.get("recommendation") == "Highly Recommended")

        metric_row(
            [
                ("Candidates", str(len(candidates)), None),
                ("Average AI Score", f"{avg_score:.0f}", None),
                ("Top Score", f"{best}", None),
                ("Highly Recommended", str(highly), None),
            ]
        )

        st.markdown("### Rankings overview")
        render_ranking_bar_chart(
            sorted(candidates, key=lambda c: extract_ai_score(c["analysis"]), reverse=True),
            score_key="ai_score",
        )

        latest = candidates[-1]["analysis"]
        ai_score = extract_ai_score(latest)
        col1, col2 = st.columns([1, 2])
        with col1:
            render_score_gauge(ai_score, "Latest AI Score")
        with col2:
            rec = latest.get("recommendation", "Consider")
            st.markdown("**Latest recommendation**")
            st.markdown(recommendation_badge(rec), unsafe_allow_html=True)
            evaluation = latest.get("evaluation", {})
            st.write(evaluation.get("summary") or evaluation.get("overall_assessment", "—"))
    else:
        show_info(
            "Upload resumes on **Resume Upload**, configure a job description, "
            "then run **Run batch analysis** to start LangGraph + Gemini screening."
        )
        metric_row(
            [
                ("Candidates", "0", None),
                ("Job configured", "Yes" if st.session_state.job_description else "No", None),
                ("Backend", "Online" if st.session_state.backend_connected else "Unknown", None),
            ]
        )
