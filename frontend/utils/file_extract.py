from __future__ import annotations


class FileExtractionError(Exception):
    pass


def extract_pdf_text(file_bytes: bytes) -> str:
    try:
        import fitz
    except ModuleNotFoundError as exc:
        raise FileExtractionError(
            "PDF support requires pymupdf. Run: pip install pymupdf"
        ) from exc

    try:
        document = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        raise FileExtractionError("The PDF resume is corrupted or unreadable.") from exc

    try:
        pages = [page.get_text("text") for page in document if page.get_text("text")]
        if not pages:
            raise FileExtractionError("No text could be extracted from the PDF.")
        return "\n".join(pages)
    except FileExtractionError:
        raise
    except Exception as exc:
        raise FileExtractionError("The PDF resume could not be processed.") from exc
    finally:
        document.close()


def extract_docx_text(file_bytes: bytes) -> str:
    try:
        from docx import Document
    except ModuleNotFoundError as exc:
        raise FileExtractionError(
            "DOCX support requires python-docx. Run: pip install python-docx"
        ) from exc

    from io import BytesIO

    try:
        document = Document(BytesIO(file_bytes))
        lines = [p.text.strip() for p in document.paragraphs if p.text.strip()]
        if not lines:
            raise FileExtractionError("No text could be extracted from the DOCX file.")
        return "\n".join(lines)
    except FileExtractionError:
        raise
    except Exception as exc:
        raise FileExtractionError("The DOCX resume could not be processed.") from exc


def extract_text_from_bytes(filename: str, file_bytes: bytes) -> str:
    lower = filename.lower()
    if lower.endswith((".txt", ".md")):
        return file_bytes.decode("utf-8", errors="replace")
    if lower.endswith(".pdf"):
        return extract_pdf_text(file_bytes)
    if lower.endswith(".docx"):
        return extract_docx_text(file_bytes)
    raise FileExtractionError(
        f"Unsupported file type: {filename}. Use PDF, DOCX, TXT, or MD."
    )
