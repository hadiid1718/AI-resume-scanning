from __future__ import annotations

import logging

from backend.app.modules.file_storage import DuplicateUploadError, FileStorage, UploadMetadata
from backend.app.modules.file_validator import FileValidator


logger = logging.getLogger(__name__)


class UploadService:
    def __init__(self, validator: FileValidator | None = None, storage: FileStorage | None = None) -> None:
        self.validator = validator or FileValidator()
        self.storage = storage or FileStorage()

    def upload_resume(self, filename: str, content: bytes, content_type: str | None = None) -> UploadMetadata:
        logger.debug("Validating resume upload filename=%s content_type=%s", filename, content_type)
        self.validator.validate(filename=filename, content=content, content_type=content_type)

        try:
            return self.storage.store(filename=filename, content=content, content_type=content_type)
        except DuplicateUploadError:
            logger.info("Rejected duplicate resume upload filename=%s", filename)
            raise
        except Exception:
            logger.exception("Unexpected error while storing resume filename=%s", filename)
            raise
