import streamlit as st


def metric_row(items: list[tuple[str, str, str | None]]) -> None:
    cols = st.columns(len(items))
    for col, (label, value, delta) in zip(cols, items):
        col.metric(label=label, value=value, delta=delta)


def rank_badge(rank: str) -> str:
    return rank.replace("_", " ").title()


def recommendation_badge(label: str) -> str:
    colors = {
        "Highly Recommended": "#16a34a",
        "Recommended": "#2563eb",
        "Consider": "#ca8a04",
        "Not Recommended": "#dc2626",
    }
    color = colors.get(label, "#64748b")
    return f'<span style="color:{color};font-weight:600;">{label}</span>'
