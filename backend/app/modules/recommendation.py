from __future__ import annotations


def score_to_recommendation(score: int | float) -> str:
    value = int(round(float(score)))
    if value >= 80:
        return "Highly Recommended"
    if value >= 65:
        return "Recommended"
    if value >= 50:
        return "Consider"
    return "Not Recommended"


def extract_ai_score(analysis: dict) -> int:
    ai = analysis.get("ai_evaluation") or {}
    if ai.get("score") is not None:
        return int(ai["score"])
    evaluation = analysis.get("evaluation") or {}
    if evaluation.get("score") is not None:
        return int(evaluation["score"])
    match = analysis.get("match_result") or {}
    return int(round(float(match.get("score", 0))))
