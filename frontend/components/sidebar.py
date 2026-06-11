from __future__ import annotations

import streamlit as st

from frontend.components.navigation import render_navigation
from frontend.services.api_client import APIClient, APIError
from frontend.utils.session_state import get_candidates, init_session_state


def render_sidebar(page_names: list[str] | None = None) -> str | None:
    init_session_state()

    with st.sidebar:
        st.markdown(
            """
            <div style="padding:0.5rem 0 1rem 0;">
                <span style="font-size:1.4rem;font-weight:700;">Resume Scanner</span>
                <div style="color:#64748b;font-size:0.85rem;margin-top:0.25rem;">
                    AI-powered candidate matching
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        st.session_state.backend_url = st.text_input(
            "Backend API URL",
            value=st.session_state.backend_url,
            help="FastAPI server address (default: http://localhost:8000)",
        )

        client = APIClient(st.session_state.backend_url)
        if st.button("Check connection", use_container_width=True):
            try:
                health = client.health()
                st.session_state.backend_connected = True
                st.success(f"Connected — {health.get('app_name', 'API')}")
            except APIError as exc:
                st.session_state.backend_connected = False
                st.error(str(exc))

        status = st.session_state.backend_connected
        if status is True:
            st.caption("Backend online")
        elif status is False:
            st.caption("Backend offline — local fallback available")
        else:
            st.caption("Connection not checked")

        st.divider()

        candidates = get_candidates()
        st.markdown("**Session overview**")
        st.caption(f"Candidates analyzed: **{len(candidates)}**")
        st.caption(f"Job title: **{st.session_state.job_title or '—'}**")

        if candidates and st.button("Clear all candidates", use_container_width=True):
            from frontend.utils.session_state import clear_candidates

            clear_candidates()
            st.rerun()

        selected = None
        if page_names:
            st.divider()
            selected = render_navigation(page_names, in_sidebar=True)

        st.divider()
        st.caption("v1.0 · AI Resume Scanning System")

    return selected
