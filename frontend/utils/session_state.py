from __future__ import annotations

from typing import Any

import streamlit as st

from frontend.utils.config import get_backend_url


def init_session_state() -> None:
    defaults: dict[str, Any] = {
        "backend_url": get_backend_url(),
        "backend_connected": None,
        "resume_text": "",
        "resume_metadata": None,
        "parsed_resume": None,
        "candidate": None,
        "job_title": "Python Backend Engineer",
        "job_description": "",
        "parsed_job": None,
        "candidates": [],
        "current_analysis": None,
        "selected_candidate_index": 0,
        "last_error": None,
        "batch_resume_texts": [],
        "analysis_in_progress": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_candidates() -> list[dict]:
    return st.session_state.get("candidates", [])


def add_candidate(analysis: dict) -> None:
    from frontend.utils.scoring import extract_ai_score, score_to_recommendation

    candidate = analysis.get("candidate", {})
    ai_score = extract_ai_score(analysis)
    recommendation = analysis.get("recommendation") or score_to_recommendation(ai_score)
    analysis["ai_score"] = ai_score
    analysis["recommendation"] = recommendation

    name = candidate.get("full_name") or f"Candidate {len(st.session_state.candidates) + 1}"
    entry = {
        "id": len(st.session_state.candidates),
        "name": name,
        "ai_score": ai_score,
        "recommendation": recommendation,
        "analysis": analysis,
    }
    st.session_state.candidates.append(entry)
    st.session_state.current_analysis = analysis
    st.session_state.selected_candidate_index = entry["id"]
    st.session_state.candidate = candidate
    st.session_state.parsed_resume = analysis.get("parsed_resume")
    st.session_state.parsed_job = analysis.get("job")


def clear_candidates() -> None:
    st.session_state.candidates = []
    st.session_state.current_analysis = None
    st.session_state.selected_candidate_index = 0
    st.session_state.candidate = None


def select_candidate(index: int) -> None:
    candidates = get_candidates()
    if 0 <= index < len(candidates):
        st.session_state.selected_candidate_index = index
        st.session_state.current_analysis = candidates[index]["analysis"]
        st.session_state.candidate = candidates[index]["analysis"].get("candidate")


def set_error(message: str | None) -> None:
    st.session_state.last_error = message


def get_selected_analysis() -> dict | None:
    candidates = get_candidates()
    index = st.session_state.get("selected_candidate_index", 0)
    if candidates and 0 <= index < len(candidates):
        return candidates[index]["analysis"]
    return st.session_state.get("current_analysis")
