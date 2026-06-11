from __future__ import annotations

from typing import Any, TypedDict


class ResumePipelineState(TypedDict, total=False):
    resume_text: str
    job_title: str
    job_description: str
    parsed_resume: dict[str, Any]
    candidate: dict[str, Any]
    job: dict[str, Any]
    match_result: dict[str, Any]
    ai_evaluation: dict[str, Any]
    rank_result: dict[str, Any]
    evaluation: dict[str, Any]
    report: dict[str, Any]
    recommendation: str
    ai_score: int
    status: str
    error: str | None
