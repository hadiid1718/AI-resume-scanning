import re
from pathlib import Path
from typing import Any

from backend.app.modules.excel_exporter import ExcelExporter
from backend.app.modules.pdf_exporter import PDFExporter


class ReportGenerator:
    def __init__(self, report_dir: str) -> None:
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.pdf_exporter = PDFExporter()
        self.excel_exporter = ExcelExporter()

    def build(self, payload: dict[str, Any]) -> dict:
        report = self._build_report(payload)
        title = report["title"]
        markdown = self._to_markdown(report)
        slug = self._slugify(title)

        report_path = self.report_dir / f"{slug}_report.md"
        pdf_path = self.report_dir / f"{slug}_report.pdf"
        csv_path = self.report_dir / f"{slug}_report.csv"
        excel_path = self.report_dir / f"{slug}_report.xlsx"

        report_path.write_text(markdown, encoding="utf-8")
        self.pdf_exporter.export(report, pdf_path)
        self.excel_exporter.export_csv(report, csv_path)
        self.excel_exporter.export_xlsx(report, excel_path)

        return {
            "title": title,
            "report_path": str(report_path),
            "pdf_path": str(pdf_path),
            "csv_path": str(csv_path),
            "excel_path": str(excel_path),
            "markdown": markdown,
            "summary": report["candidate_summary"],
            "ranking": report["ranking"],
            "skill_gaps": report["skill_gaps"],
        }

    def _build_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        candidate = payload.get("candidate", {})
        job = payload.get("job", {})
        match_result = payload.get("match_result", {})
        rank_result = payload.get("rank_result", {})
        evaluation = payload.get("evaluation", {})
        ranking = self._ranking_rows(payload)
        skill_gaps = self._skill_gap_rows(match_result, evaluation)
        score_rows = self._score_rows(match_result, rank_result, evaluation)

        title = job.get("title") or "Resume Analysis Report"
        candidate_name = (
            candidate.get("full_name")
            or candidate.get("candidate_name")
            or candidate.get("name")
            or evaluation.get("candidate_name")
            or "Unknown"
        )

        return {
            "title": title,
            "candidate_summary": {
                "name": candidate_name,
                "email": candidate.get("email") or "Unknown",
                "phone": candidate.get("phone_number") or candidate.get("phone") or "Unknown",
                "location": candidate.get("location") or "Unknown",
                "experience_years": candidate.get("experience_years") or candidate.get("years_experience") or "Unknown",
                "job_title": title,
                "assessment": evaluation.get("overall_assessment") or evaluation.get("verdict") or "unknown",
            },
            "scores": score_rows,
            "ranking": ranking,
            "skill_gaps": skill_gaps,
            "recommendations": evaluation.get("recommendations", []) or ["No recommendations generated."],
            "charts": [
                {
                    "title": "Score Breakdown",
                    "items": [
                        {"label": row["metric"], "value": row["score"]}
                        for row in score_rows
                    ],
                },
                {
                    "title": "Skill Coverage",
                    "items": [
                        {"label": "Matched Skills", "value": len(match_result.get("overlap_skills", []))},
                        {"label": "Missing Skills", "value": len(match_result.get("missing_skills", []))},
                    ],
                },
            ],
        }

    def _to_markdown(self, report: dict[str, Any]) -> str:
        summary = report["candidate_summary"]
        score_table = self._markdown_table(["Metric", "Score"], report["scores"])
        ranking_table = self._markdown_table(
            ["Rank", "Candidate", "Weighted Score", "Tier"],
            report["ranking"],
        )
        skill_gap_table = self._markdown_table(
            ["Skill", "Status", "Source"],
            report["skill_gaps"],
        )
        recommendations = [f"- {item}" for item in report["recommendations"]]
        if not recommendations:
            recommendations = ["- No recommendations generated."]

        return "\n".join(
            [
                f"# {report['title']}",
                "",
                "## Candidate Summary",
                f"- Name: {summary['name']}",
                f"- Email: {summary['email']}",
                f"- Phone: {summary['phone']}",
                f"- Location: {summary['location']}",
                f"- Experience Years: {summary['experience_years']}",
                f"- Assessment: {summary['assessment']}",
                "",
                "## Score Table",
                score_table,
                "",
                "## Ranking Report",
                ranking_table,
                "",
                "## Skill Gap Report",
                skill_gap_table,
                "",
                "## Charts",
                *self._markdown_charts(report["charts"]),
                "",
                "## Recommendations",
                *recommendations,
            ]
        )

    def _ranking_rows(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        candidate = payload.get("candidate", {})
        evaluation = payload.get("evaluation", {})
        rank_result = payload.get("rank_result", {})
        raw_ranking = (
            payload.get("ranking")
            or payload.get("ranked_candidates")
            or rank_result.get("ranked_candidates")
            or rank_result.get("top_candidates")
        )

        if isinstance(raw_ranking, list) and raw_ranking:
            return [
                {
                    "rank": item.get("rank", index),
                    "candidate": item.get("candidate_name") or item.get("name") or f"Candidate {index}",
                    "weighted_score": item.get("weighted_score", item.get("score", 0)),
                    "tier": item.get("rank_label") or item.get("rank_tier") or item.get("rank", "unknown"),
                }
                for index, item in enumerate(raw_ranking, start=1)
            ]

        return [
            {
                "rank": rank_result.get("rank", "N/A"),
                "candidate": (
                    candidate.get("full_name")
                    or candidate.get("name")
                    or evaluation.get("candidate_name")
                    or "Unknown"
                ),
                "weighted_score": rank_result.get("weighted_score", rank_result.get("score", 0)),
                "tier": rank_result.get("rank", "unknown"),
            }
        ]

    @staticmethod
    def _skill_gap_rows(match_result: dict[str, Any], evaluation: dict[str, Any]) -> list[dict[str, Any]]:
        rows = [
            {"skill": skill, "status": "Matched", "source": "match_result"}
            for skill in match_result.get("overlap_skills", [])
        ]
        rows.extend(
            {"skill": skill, "status": "Missing", "source": "match_result"}
            for skill in match_result.get("missing_skills", [])
        )
        rows.extend(
            {"skill": gap, "status": "Gap", "source": "evaluation"}
            for gap in evaluation.get("gaps", []) or evaluation.get("weaknesses", [])
        )
        return rows or [{"skill": "No skill gaps identified", "status": "N/A", "source": "system"}]

    @staticmethod
    def _score_rows(
        match_result: dict[str, Any],
        rank_result: dict[str, Any],
        evaluation: dict[str, Any],
    ) -> list[dict[str, Any]]:
        rows = [
            {"metric": "Match Score", "score": match_result.get("score", 0)},
            {"metric": "Ranking Score", "score": rank_result.get("weighted_score", rank_result.get("score", 0))},
        ]
        if "score" in evaluation:
            rows.append({"metric": "AI Evaluation Score", "score": evaluation.get("score", 0)})
        return rows

    @staticmethod
    def _markdown_table(headers: list[str], rows: list[dict[str, Any]]) -> str:
        keys = [header.lower().replace(" ", "_") for header in headers]
        lines = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
        ]
        for row in rows:
            lines.append("| " + " | ".join(str(row.get(key, "")) for key in keys) + " |")
        return "\n".join(lines)

    @staticmethod
    def _markdown_charts(charts: list[dict[str, Any]]) -> list[str]:
        lines: list[str] = []
        for chart in charts:
            lines.append(f"### {chart['title']}")
            for item in chart["items"]:
                value = float(item.get("value") or 0)
                bar = "#" * min(30, int(round(value / 100 * 30 if value <= 100 else value)))
                lines.append(f"- {item['label']}: {bar} {value:g}")
            lines.append("")
        return lines

    @staticmethod
    def _slugify(value: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
        return slug or "resume_analysis"
