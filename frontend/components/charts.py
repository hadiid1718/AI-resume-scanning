from __future__ import annotations

import pandas as pd
import streamlit as st


def render_score_gauge(score: float, title: str = "Match Score") -> None:
    st.markdown(f"**{title}**")
    progress = min(max(score / 100, 0.0), 1.0)
    st.progress(progress, text=f"{score:.1f}%")

    if score >= 80:
        color = "#16a34a"
    elif score >= 60:
        color = "#ca8a04"
    elif score >= 40:
        color = "#ea580c"
    else:
        color = "#dc2626"

    st.markdown(
        f"""
        <div style="
            text-align:center;
            font-size:2rem;
            font-weight:700;
            color:{color};
            margin-top:-0.5rem;
        ">{score:.1f}%</div>
        """,
        unsafe_allow_html=True,
    )


def render_skills_chart(overlap: list[str], missing: list[str]) -> None:
    data = pd.DataFrame(
        {
            "Category": ["Matched Skills", "Missing Skills"],
            "Count": [len(overlap), len(missing)],
        }
    )
    st.bar_chart(data.set_index("Category"), height=220)


def render_ranking_bar_chart(candidates: list[dict], score_key: str = "score") -> None:
    if not candidates:
        st.caption("No candidates to chart yet.")
        return

    rows = []
    for entry in candidates:
        analysis = entry.get("analysis", {})
        if score_key == "ai_score":
            from frontend.utils.scoring import extract_ai_score

            score = float(extract_ai_score(analysis))
        else:
            match = analysis.get("match_result", {})
            score = float(match.get("score", 0))
        rows.append(
            {
                "Candidate": entry.get("name", "Unknown")[:24],
                "Score": score,
            }
        )

    df = pd.DataFrame(rows).sort_values("Score", ascending=True)
    st.bar_chart(df.set_index("Candidate"), height=max(220, len(rows) * 40))


def render_match_breakdown(match_result: dict) -> None:
    overlap = match_result.get("overlap_skills", [])
    missing = match_result.get("missing_skills", [])

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Matched Skills**")
        if overlap:
            st.markdown(" ".join(f"`{s}`" for s in overlap[:20]))
            if len(overlap) > 20:
                st.caption(f"+{len(overlap) - 20} more")
        else:
            st.caption("No overlapping skills detected.")

    with col2:
        st.markdown("**Missing Skills**")
        if missing:
            st.markdown(" ".join(f"`{s}`" for s in missing[:20]))
            if len(missing) > 20:
                st.caption(f"+{len(missing) - 20} more")
        else:
            st.caption("No skill gaps identified.")
