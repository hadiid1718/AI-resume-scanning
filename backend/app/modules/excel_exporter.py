"""CSV and Excel exporters for resume analysis reports."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


class ExcelExporter:
    """Export report data to CSV and XLSX using the Python standard library."""

    def export_csv(self, report: dict[str, Any], output_path: str | Path) -> str:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with output.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Candidate Summary"])
            for key, value in report["candidate_summary"].items():
                writer.writerow([key.replace("_", " ").title(), value])

            writer.writerow([])
            writer.writerow(["Score Table"])
            writer.writerow(["Metric", "Score"])
            for row in report["scores"]:
                writer.writerow([row.get("metric", ""), row.get("score", "")])

            writer.writerow([])
            writer.writerow(["Ranking Report"])
            writer.writerow(["Rank", "Candidate", "Weighted Score", "Tier"])
            for row in report["ranking"]:
                writer.writerow([
                    row.get("rank", ""),
                    row.get("candidate", ""),
                    row.get("weighted_score", ""),
                    row.get("tier", ""),
                ])

            writer.writerow([])
            writer.writerow(["Skill Gap Report"])
            writer.writerow(["Skill", "Status", "Source"])
            for row in report["skill_gaps"]:
                writer.writerow([row.get("skill", ""), row.get("status", ""), row.get("source", "")])

            writer.writerow([])
            writer.writerow(["Chart Data"])
            for chart in report["charts"]:
                writer.writerow([chart["title"]])
                writer.writerow(["Label", "Value", "Bar"])
                for item in chart["items"]:
                    writer.writerow([item.get("label", ""), item.get("value", ""), self._bar(item.get("value", 0))])

        return str(output)

    def export_xlsx(self, report: dict[str, Any], output_path: str | Path) -> str:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        sheets = [
            (
                "Summary",
                [["Candidate Summary"]]
                + [[key.replace("_", " ").title(), value] for key, value in report["candidate_summary"].items()],
            ),
            (
                "Ranking",
                [["Rank", "Candidate", "Weighted Score", "Tier"]]
                + [
                    [row.get("rank", ""), row.get("candidate", ""), row.get("weighted_score", ""), row.get("tier", "")]
                    for row in report["ranking"]
                ],
            ),
            (
                "Skill Gaps",
                [["Skill", "Status", "Source"]]
                + [[row.get("skill", ""), row.get("status", ""), row.get("source", "")] for row in report["skill_gaps"]],
            ),
            (
                "Charts",
                self._chart_sheet_rows(report["charts"]),
            ),
        ]

        with ZipFile(output, "w", ZIP_DEFLATED) as workbook:
            workbook.writestr("[Content_Types].xml", self._content_types(len(sheets)))
            workbook.writestr("_rels/.rels", self._root_relationships())
            workbook.writestr("xl/workbook.xml", self._workbook(sheets))
            workbook.writestr("xl/_rels/workbook.xml.rels", self._workbook_relationships(len(sheets)))
            workbook.writestr("xl/styles.xml", self._styles())
            for index, (_, rows) in enumerate(sheets, start=1):
                workbook.writestr(f"xl/worksheets/sheet{index}.xml", self._worksheet(rows))

        return str(output)

    def _chart_sheet_rows(self, charts: list[dict[str, Any]]) -> list[list[Any]]:
        rows: list[list[Any]] = [["Chart", "Label", "Value", "Bar"]]
        for chart in charts:
            for item in chart["items"]:
                value = item.get("value", 0)
                rows.append([chart["title"], item.get("label", ""), value, self._bar(value)])
        return rows

    @staticmethod
    def _bar(value: Any) -> str:
        try:
            number = float(value)
        except (TypeError, ValueError):
            number = 0.0
        units = int(round(number / 5 if number <= 100 else min(number, 100) / 5))
        return "#" * max(0, min(20, units))

    @staticmethod
    def _content_types(sheet_count: int) -> str:
        sheet_overrides = "".join(
            f'<Override PartName="/xl/worksheets/sheet{index}.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            for index in range(1, sheet_count + 1)
        )
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/styles.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            f"{sheet_overrides}"
            "</Types>"
        )

    @staticmethod
    def _root_relationships() -> str:
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            'Target="xl/workbook.xml"/>'
            "</Relationships>"
        )

    @staticmethod
    def _workbook(sheets: list[tuple[str, list[list[Any]]]]) -> str:
        sheet_xml = "".join(
            f'<sheet name="{escape(name)}" sheetId="{index}" r:id="rId{index}"/>'
            for index, (name, _) in enumerate(sheets, start=1)
        )
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f"<sheets>{sheet_xml}</sheets>"
            "</workbook>"
        )

    @staticmethod
    def _workbook_relationships(sheet_count: int) -> str:
        relationships = "".join(
            f'<Relationship Id="rId{index}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{index}.xml"/>'
            for index in range(1, sheet_count + 1)
        )
        relationships += (
            f'<Relationship Id="rId{sheet_count + 1}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
            'Target="styles.xml"/>'
        )
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f"{relationships}"
            "</Relationships>"
        )

    @staticmethod
    def _styles() -> str:
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            "<fonts count=\"1\"><font><sz val=\"11\"/><name val=\"Calibri\"/></font></fonts>"
            "<fills count=\"1\"><fill><patternFill patternType=\"none\"/></fill></fills>"
            "<borders count=\"1\"><border/></borders>"
            "<cellStyleXfs count=\"1\"><xf/></cellStyleXfs>"
            "<cellXfs count=\"1\"><xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"0\" xfId=\"0\"/></cellXfs>"
            "</styleSheet>"
        )

    def _worksheet(self, rows: list[list[Any]]) -> str:
        row_xml = "".join(
            f'<row r="{row_index}">'
            + "".join(
                self._cell(row_index, column_index, value)
                for column_index, value in enumerate(row, start=1)
            )
            + "</row>"
            for row_index, row in enumerate(rows, start=1)
        )
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            "<sheetData>"
            f"{row_xml}"
            "</sheetData>"
            "</worksheet>"
        )

    def _cell(self, row: int, column: int, value: Any) -> str:
        ref = f"{self._column_name(column)}{row}"
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return f'<c r="{ref}"><v>{value}</v></c>'
        return f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'

    @staticmethod
    def _column_name(index: int) -> str:
        name = ""
        while index:
            index, remainder = divmod(index - 1, 26)
            name = chr(65 + remainder) + name
        return name
