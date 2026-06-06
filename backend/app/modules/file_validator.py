from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class FileValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ValidationConfig:
    max_file_size_bytes: int = 10 * 1024 * 1024


class FileValidator:
    allowed_extensions = {".pdf", ".docx"}
    allowed_content_types = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    def __init__(self, config: ValidationConfig | None = None) -> None:
        self.config = config or ValidationConfig()

    def validate(self, filename: str, content: bytes, content_type: str | None = None) -> None:
        self._validate_filename(filename)
        self._validate_extension(filename)
        self._validate_content_type(content_type)
        self._validate_size(content)

    def _validate_filename(self, filename: str) -> None:
        if not filename or not filename.strip():
            raise FileValidationError("A resume filename is required.")

        if Path(filename).name != filename:
            raise FileValidationError("The filename must not include directory segments.")

    def _validate_extension(self, filename: str) -> None:
        extension = Path(filename).suffix.lower()
        if extension not in self.allowed_extensions:
            raise FileValidationError("Only PDF and DOCX resumes are supported.")

    def _validate_content_type(self, content_type: str | None) -> None:
        if content_type and content_type.lower() not in self.allowed_content_types:
            raise FileValidationError("The uploaded file content type is not allowed.")

    def _validate_size(self, content: bytes) -> None:
        if not content:
            raise FileValidationError("The uploaded file is empty.")

        if len(content) > self.config.max_file_size_bytes:
            raise FileValidationError(
                f"The uploaded file exceeds the maximum size of {self.config.max_file_size_bytes} bytes."
            )
