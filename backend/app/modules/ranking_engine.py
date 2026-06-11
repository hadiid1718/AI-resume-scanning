"""Module 10 - Candidate ranking engine.

Ranks candidate evaluation results with configurable weighted scoring and stable
tie handling. The engine accepts both the newer AI evaluation payloads and the
older match-result shape used by the existing ``/rank`` endpoint.
"""

from __future__ import annotations

from typing import Any


class RankingEngine:
    """Rank candidate evaluation results using configurable weighted scoring."""

    DEFAULT_WEIGHTS: dict[str, float] = {"score": 1.0}

    _CANDIDATE_ID_KEYS = ("candidate_id", "id", "email")
    _CANDIDATE_NAME_KEYS = ("candidate_name", "full_name", "name")

    def __init__(
        self,
        weights: dict[str, float] | None = None,
        tie_precision: int = 2,
    ) -> None:
        self.weights = self._normalize_weights(weights or self.DEFAULT_WEIGHTS)
        self.tie_precision = tie_precision

    def rank(
        self,
        evaluation_result: dict[str, Any] | list[dict[str, Any]],
        weights: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Rank one result for backward compatibility, or rank a batch.

        Existing pipeline code passes a single match result and expects a tier
        label. Passing a list returns the full candidate ranking output.
        """
        if isinstance(evaluation_result, list):
            ranked = self.rank_candidates(evaluation_result, weights=weights)
            return {
                "ranked_candidates": ranked,
                "top_candidates": ranked,
                "total": len(ranked),
                "weights": self._normalize_weights(weights or self.weights),
            }

        score_data = self.score_candidate(evaluation_result, weights=weights)
        return {
            "rank": self._score_tier(score_data["weighted_score"]),
            "score": score_data["weighted_score"],
            "weighted_score": score_data["weighted_score"],
            "component_scores": score_data["component_scores"],
            "weights": score_data["weights"],
        }

    def score_candidate(
        self,
        evaluation_result: dict[str, Any],
        weights: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Calculate a weighted score for one candidate evaluation result."""
        active_weights = self._normalize_weights(weights or self.weights)
        component_scores = {
            field: self._extract_score(evaluation_result, field)
            for field in active_weights
        }
        weighted_score = sum(
            component_scores[field] * weight
            for field, weight in active_weights.items()
        )

        return {
            "candidate_id": self._first_present(evaluation_result, self._CANDIDATE_ID_KEYS),
            "candidate_name": self._first_present(evaluation_result, self._CANDIDATE_NAME_KEYS) or "N/A",
            "weighted_score": round(weighted_score, 2),
            "component_scores": component_scores,
            "weights": active_weights,
            "source": evaluation_result,
        }

    def rank_candidates(
        self,
        evaluation_results: list[dict[str, Any]],
        weights: dict[str, float] | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Return candidates sorted by weighted score with tied ranks preserved."""
        scored = [
            {
                **self.score_candidate(result, weights=weights),
                "original_position": index,
            }
            for index, result in enumerate(evaluation_results)
        ]
        scored.sort(key=lambda item: (-item["weighted_score"], item["original_position"]))

        previous_score: float | None = None
        previous_rank = 0
        for index, item in enumerate(scored, start=1):
            comparable_score = round(item["weighted_score"], self.tie_precision)
            if previous_score is None or comparable_score != previous_score:
                previous_rank = index
                previous_score = comparable_score

            item["rank"] = previous_rank
            item["rank_label"] = self._score_tier(item["weighted_score"])
            item["is_tied"] = self._has_tie(scored, comparable_score)

        if limit is not None:
            return scored[: max(0, limit)]
        return scored

    def top_candidates(
        self,
        evaluation_results: list[dict[str, Any]],
        weights: dict[str, float] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Generate a top-candidate list from evaluation results."""
        return self.rank_candidates(evaluation_results, weights=weights, limit=limit)

    @staticmethod
    def _normalize_weights(weights: dict[str, float]) -> dict[str, float]:
        if not weights:
            raise ValueError("At least one ranking weight is required.")

        cleaned: dict[str, float] = {}
        for field, weight in weights.items():
            number = float(weight)
            if number < 0:
                raise ValueError(f"Ranking weight for '{field}' cannot be negative.")
            if number > 0:
                cleaned[field] = number

        total = sum(cleaned.values())
        if total <= 0:
            raise ValueError("At least one ranking weight must be greater than zero.")

        return {field: weight / total for field, weight in cleaned.items()}

    @classmethod
    def _extract_score(cls, result: dict[str, Any], field: str) -> float:
        value = result.get(field)
        if value is None and "." in field:
            value = cls._nested_get(result, field)
        return cls._clamp_score(value)

    @staticmethod
    def _nested_get(result: dict[str, Any], path: str) -> Any:
        current: Any = result
        for part in path.split("."):
            if not isinstance(current, dict):
                return None
            current = current.get(part)
        return current

    @staticmethod
    def _clamp_score(value: Any) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            number = 0.0
        return round(max(0.0, min(100.0, number)), 2)

    @staticmethod
    def _first_present(result: dict[str, Any], keys: tuple[str, ...]) -> Any:
        for key in keys:
            value = result.get(key)
            if value not in (None, ""):
                return value
        return None

    @staticmethod
    def _score_tier(score: float) -> str:
        if score >= 80:
            return "excellent"
        if score >= 60:
            return "strong"
        if score >= 40:
            return "moderate"
        return "weak"

    def _has_tie(self, scored: list[dict[str, Any]], score: float) -> bool:
        return sum(
            1
            for item in scored
            if round(item["weighted_score"], self.tie_precision) == score
        ) > 1
