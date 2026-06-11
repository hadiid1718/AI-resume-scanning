from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.modules.docx_extractor import DOCXExtractor
    from backend.app.modules.pdf_extractor import PDFExtractor


logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    pass


@dataclass(frozen=True)
class ExtractionResult:
    filename: str
    file_type: str
    text: str


class ExtractionService:
    def __init__(
        self,
        pdf_extractor: PDFExtractor | None = None,
        docx_extractor: DOCXExtractor | None = None,
    ) -> None:
        self._pdf_extractor = pdf_extractor
        self._docx_extractor = docx_extractor

    @property
    def pdf_extractor(self) -> PDFExtractor:
        if self._pdf_extractor is None:
            from backend.app.modules.pdf_extractor import PDFExtractor

            self._pdf_extractor = PDFExtractor()
        return self._pdf_extractor

    @property
    def docx_extractor(self) -> DOCXExtractor:
        if self._docx_extractor is None:
            from backend.app.modules.docx_extractor import DOCXExtractor

            self._docx_extractor = DOCXExtractor()
        return self._docx_extractor

    def extract_from_file(self, filename: str, file_bytes: bytes) -> ExtractionResult:
        from backend.app.modules.docx_extractor import DOCXExtractionError
        from backend.app.modules.pdf_extractor import PDFExtractionError

        file_type = self._detect_file_type(filename)

        try:
            if file_type == "pdf":
                raw_text = self.pdf_extractor.extract(file_bytes)
            elif file_type == "docx":
                raw_text = self.docx_extractor.extract(file_bytes)
            else:
                raise ExtractionError("Only PDF and DOCX resumes are supported.")
        except (PDFExtractionError, DOCXExtractionError) as exc:
            logger.warning("Resume extraction failed for %s: %s", filename, exc)
            raise ExtractionError(str(exc)) from exc
        except ExtractionError:
            raise
        except Exception as exc:
            logger.exception("Unexpected extraction failure for %s", filename)
            raise ExtractionError("Unable to extract text from the uploaded resume.") from exc

        return ExtractionResult(
            filename=Path(filename).name,
            file_type=file_type,
            text=self._normalize_text(raw_text),
        )

    def extract_text(self, text: str) -> str:
        return self._normalize_text(text)

    def _detect_file_type(self, filename: str) -> str:
        extension = Path(filename).suffix.lower()
        if extension == ".pdf":
            return "pdf"
        if extension == ".docx":
            return "docx"
        raise ExtractionError("Only PDF and DOCX resumes are supported.")

    def _normalize_text(self, raw_text: str) -> str:
        normalized_lines: list[str] = []

        for line in raw_text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
            cleaned_line = " ".join(line.split())
            if cleaned_line:
                normalized_lines.append(cleaned_line)
            elif normalized_lines and normalized_lines[-1] != "":
                normalized_lines.append("")

        while normalized_lines and normalized_lines[0] == "":
            normalized_lines.pop(0)

        while normalized_lines and normalized_lines[-1] == "":
            normalized_lines.pop()

        return "\n".join(normalized_lines)
