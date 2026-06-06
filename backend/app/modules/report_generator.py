from pathlib import Path
from typing import Any


class ReportGenerator:
    def __init__(self, report_dir: str) -> None:
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def build(self, payload: dict[str, Any]) -> dict:
        title = payload.get("job", {}).get("title") or "Resume Analysis Report"
        markdown = self._to_markdown(payload)
        report_path = self.report_dir / f"{title.replace(' ', '_').lower()}_report.md"
        report_path.write_text(markdown, encoding="utf-8")

        return {
            "title": title,
            "report_path": str(report_path),
            "markdown": markdown,
        }

    def _to_markdown(self, payload: dict[str, Any]) -> str:
        candidate = payload.get("candidate", {})
        job = payload.get("job", {})
        match_result = payload.get("match_result", {})
        evaluation = payload.get("evaluation", {})
        recommendations = [f"- {item}" for item in evaluation.get("recommendations", [])]
        if not recommendations:
            recommendations = ["- No recommendations generated."]

        return "\n".join(
            [
                f"# {job.get('title', 'Resume Analysis Report')}",
                "",
                f"## Candidate\n- Name: {candidate.get('full_name') or 'Unknown'}\n- Email: {candidate.get('email') or 'Unknown'}",
                "",
                f"## Match Score\n- Score: {match_result.get('score', 0.0)}\n- Rank: {payload.get('rank_result', {}).get('rank', 'unknown')}",
                "",
                f"## AI Evaluation\n- Assessment: {evaluation.get('overall_assessment', 'unknown')}",
                "",
                "## Recommendations",
                *recommendations,
            ]
        )
