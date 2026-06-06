from __future__ import annotations

import logging

import fitz


logger = logging.getLogger(__name__)


class PDFExtractionError(Exception):
    pass


class PDFExtractor:
    def extract(self, pdf_bytes: bytes) -> str:
        try:
            document = fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception as exc:
            logger.exception("Failed to open PDF resume")
            raise PDFExtractionError("The PDF resume is corrupted or unreadable.") from exc

        try:
            pages: list[str] = []
            for page in document:
                page_text = page.get_text("text")
                if page_text:
                    pages.append(page_text)
            return "\n".join(pages)
        except Exception as exc:
            logger.exception("Failed to extract text from PDF resume")
            raise PDFExtractionError("The PDF resume could not be processed.") from exc
        finally:
            document.close()
