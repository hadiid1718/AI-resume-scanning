from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from frontend.components.alerts import show_error, show_info, show_warning
from frontend.components.loading import loading_context
from frontend.services.api_client import APIClient, APIError
from frontend.utils.session_state import get_candidates, get_selected_analysis, init_session_state
from frontend.utils.styles import page_header


def _read_file_bytes(path_str: str) -> bytes | None:
    if not path_str:
        return None
    path = Path(path_str)
    if not path.is_file():
        project_root = Path(__file__).resolve().parents[2]
        alt = project_root / path_str
        if alt.is_file():
            path = alt
        else:
            return None
    return path.read_bytes()


def render() -> None:
    init_session_state()
    page_header("Reports Download", "Export analysis reports in Markdown, PDF, CSV, and Excel formats")

    analysis = get_selected_analysis()
    candidates = get_candidates()

    if not analysis and not candidates:
        show_warning("No reports available yet.")
        show_info("Run an analysis from the Resume Upload page to generate reports.")
        return

    if candidates:
        names = [c["name"] for c in candidates]
        selected = st.selectbox("Select candidate report", names)
        analysis = candidates[names.index(selected)]["analysis"]

    report = analysis.get("report", {})
    if not report:
        show_warning("No report data in the selected analysis.")
        if st.button("Generate report via API"):
            client = APIClient(st.session_state.backend_url)
            payload = {
                "candidate": analysis.get("candidate", {}),
                "job": analysis.get("job", {}),
                "match_result": analysis.get("match_result", {}),
                "rank_result": analysis.get("rank_result", {}),
                "evaluation": analysis.get("evaluation", {}),
            }
            try:
                with loading_context("Generating report…"):
                    report = client.generate_report(payload)
                show_info("Report generated.")
            except APIError as exc:
                show_error(str(exc))
                return
        else:
            return

    st.markdown(f"### {report.get('title', 'Candidate Report')}")

    summary = report.get("summary") or report.get("markdown", "")[:500]
    if summary:
        with st.expander("Report preview", expanded=True):
            st.markdown(report.get("markdown", summary))

    st.markdown("### Download files")

    col1, col2, col3, col4 = st.columns(4)

    markdown_content = report.get("markdown", "")
    if markdown_content:
        col1.download_button("Download Markdown", data=markdown_content, file_name="candidate_report.md", mime="text/markdown", use_container_width=True)

    pdf_bytes = _read_file_bytes(report.get("pdf_path", ""))
    if pdf_bytes:
        col2.download_button("Download PDF", data=pdf_bytes, file_name="candidate_report.pdf", mime="application/pdf", use_container_width=True)
    else:
        col2.caption("PDF not available")

    csv_bytes = _read_file_bytes(report.get("csv_path", ""))
    if csv_bytes:
        col3.download_button("Download CSV", data=csv_bytes, file_name="candidate_report.csv", mime="text/csv", use_container_width=True)
    else:
        col3.caption("CSV not available")

    excel_bytes = _read_file_bytes(report.get("excel_path", ""))
    if excel_bytes:
        col4.download_button("Download Excel", data=excel_bytes, file_name="candidate_report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    else:
        col4.caption("Excel not available")

    if not any([markdown_content, pdf_bytes, csv_bytes, excel_bytes]):
        show_warning("Report files were not found on disk. Re-run analysis to regenerate exports.")

    st.divider()
    st.markdown("### Batch export")
    if len(candidates) > 1:
        show_info(f"Export summaries for all {len(candidates)} candidates as a combined Markdown file.")
        combined_lines = ["# Candidate Reports Summary\n"]
        for entry in candidates:
            r = entry["analysis"].get("report", {})
            combined_lines.append(f"## {entry['name']}\n")
            combined_lines.append(r.get("markdown", "_No report_"))
            combined_lines.append("\n---\n")
        combined_md = "\n".join(combined_lines)
        st.download_button(
            "Download all reports (Markdown)",
            data=combined_md,
            file_name="all_candidate_reports.md",
            mime="text/markdown",
        )
    else:
        st.caption("Analyze multiple candidates to enable batch export.")
