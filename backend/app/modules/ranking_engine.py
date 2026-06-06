class RankingEngine:
    def rank(self, match_result: dict) -> dict:
        score = float(match_result.get("score", 0.0))
        if score >= 80:
            rank = "excellent"
        elif score >= 60:
            rank = "strong"
        elif score >= 40:
            rank = "moderate"
        else:
            rank = "weak"

        return {
            "rank": rank,
            "score": score,
        }
