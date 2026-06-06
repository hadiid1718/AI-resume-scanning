from __future__ import annotations

from backend.app.modules.extraction_service import ExtractionService


class ResumeParserModule:
    def __init__(self, extraction_service: ExtractionService | None = None) -> None:
        self.extraction_service = extraction_service or ExtractionService()

    def parse_text(self, raw_text: str) -> dict:
        normalized = self.extraction_service.extract_text(raw_text)
        return {
            "raw_text": raw_text,
            "normalized_text": normalized,
            "word_count": len(normalized.split()),
        }

    def parse_pdf(self, pdf_bytes: bytes) -> dict:
        result = self.extraction_service.extract_from_file("resume.pdf", pdf_bytes)
        return {
            "raw_text": result.text,
            "normalized_text": result.text,
            "word_count": len(result.text.split()),
        }

    def parse_docx(self, docx_bytes: bytes) -> dict:
        result = self.extraction_service.extract_from_file("resume.docx", docx_bytes)
        return {
            "raw_text": result.text,
            "normalized_text": result.text,
            "word_count": len(result.text.split()),
        }
