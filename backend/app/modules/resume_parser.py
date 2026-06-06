from io import BytesIO

from pypdf import PdfReader


class ResumeParserModule:
    def parse_text(self, raw_text: str) -> dict:
        normalized = "\n".join(line.strip() for line in raw_text.splitlines() if line.strip())
        return {
            "raw_text": raw_text,
            "normalized_text": normalized,
            "word_count": len(normalized.split()),
        }

    def parse_pdf(self, pdf_bytes: bytes) -> dict:
        reader = PdfReader(BytesIO(pdf_bytes))
        extracted_text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return self.parse_text(extracted_text)
