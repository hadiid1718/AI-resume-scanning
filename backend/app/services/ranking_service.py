"""Service layer for Module 10 candidate ranking."""

from __future__ import annotations

from typing import Any

from backend.app.modules.ranking_engine import RankingEngine


class RankingService:
    """Application-facing service for ranking evaluated candidates."""

    def __init__(
        self,
        engine: RankingEngine | None = None,
        default_weights: dict[str, float] | None = None,
    ) -> None:
        self.engine = engine or RankingEngine(weights=default_weights)

    def rank_candidate(
        self,
        evaluation_result: dict[str, Any],
        weights: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Rank a single candidate evaluation result."""
        return self.engine.rank(evaluation_result, weights=weights)

    def rank_candidates(
        self,
        evaluation_results: list[dict[str, Any]],
        weights: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Rank all candidates and return a complete ranking payload."""
        ranked = self.engine.rank_candidates(evaluation_results, weights=weights)
        return self._build_response(ranked, weights)

    def top_candidates(
        self,
        evaluation_results: list[dict[str, Any]],
        limit: int = 10,
        weights: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Generate the top candidate list for a role or evaluation batch."""
        ranked = self.engine.top_candidates(
            evaluation_results,
            weights=weights,
            limit=limit,
        )
        return self._build_response(ranked, weights, limit=limit)

    def _build_response(
        self,
        ranked_candidates: list[dict[str, Any]],
        weights: dict[str, float] | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        active_weights = self.engine._normalize_weights(weights or self.engine.weights)
        return {
            "ranked_candidates": ranked_candidates,
            "top_candidates": ranked_candidates,
            "total": len(ranked_candidates),
            "limit": limit,
            "weights": active_weights,
        }
