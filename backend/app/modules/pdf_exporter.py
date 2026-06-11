"""PDF exporter using ReportLab with stdlib fallback."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class PDFExporter:
    def export(self, report: dict[str, Any], output_path: str | Path) -> str:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._export_reportlab(report, output)
        except Exception:
            self._export_simple(report, output)
        return str(output)

    def _export_reportlab(self, report: dict[str, Any], output: Path) -> None:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        doc = SimpleDocTemplate(str(output), pagesize=letter)
        styles = getSampleStyleSheet()
        story = [
            Paragraph(report.get("title", "Candidate Report"), styles["Title"]),
            Spacer(1, 12),
            Paragraph("Candidate Summary", styles["Heading2"]),
            Paragraph(str(report.get("candidate_summary", "")), styles["Normal"]),
            Spacer(1, 12),
            Paragraph("Scores", styles["Heading2"]),
        ]

        score_rows = [["Metric", "Score"]] + [
            [row.get("metric", ""), str(row.get("score", ""))] for row in report.get("scores", [])
        ]
        if len(score_rows) > 1:
            table = Table(score_rows, hAlign="LEFT")
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ]
                )
            )
            story.append(table)

        story.append(Spacer(1, 12))
        story.append(Paragraph("Recommendations", styles["Heading2"]))
        for item in report.get("recommendations", []):
            story.append(Paragraph(f"- {item}", styles["Normal"]))

        doc.build(story)

    def _export_simple(self, report: dict[str, Any], output: Path) -> None:
        from backend.app.modules.pdf_exporter_simple import SimplePDFWriter

        writer = SimplePDFWriter()
        writer.heading(report.get("title", "Report"))
        writer.text(str(report.get("candidate_summary", "")))
        for row in report.get("scores", []):
            writer.text(f"{row.get('metric')}: {row.get('score')}")
        for item in report.get("recommendations", []):
            writer.text(f"- {item}")
        output.write_bytes(writer.render())
