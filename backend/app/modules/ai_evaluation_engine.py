class AIEvaluationEngine:
    def evaluate(self, candidate: dict, job: dict, match_result: dict) -> dict:
        score = float(match_result.get("score", 0.0))
        missing_skills = match_result.get("missing_skills", [])
        recommendations = []

        if missing_skills:
            recommendations.append(f"Highlight or learn: {', '.join(missing_skills[:5])}")
        if score < 50:
            recommendations.append("Consider a role with a closer skill match or strengthen core requirements first.")

        return {
            "overall_assessment": "promising" if score >= 60 else "needs_improvement",
            "strengths": match_result.get("overlap_skills", []),
            "gaps": missing_skills,
            "recommendations": recommendations,
        }
