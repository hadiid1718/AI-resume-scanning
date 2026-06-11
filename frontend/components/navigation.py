from __future__ import annotations

import streamlit as st


def render_navigation(page_names: list[str], in_sidebar: bool = False) -> str:
    navigate_to = st.session_state.pop("_navigate_to", None)
    default_index = page_names.index(navigate_to) if navigate_to in page_names else 0

    def _render() -> str:
        st.markdown("**Navigate**")
        return st.radio(
            "Navigation",
            page_names,
            index=default_index,
            label_visibility="collapsed",
        )

    if in_sidebar:
        return _render()

    with st.sidebar:
        return _render()
