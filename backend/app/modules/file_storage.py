from __future__ import annotations

import hashlib
import json
import logging
import threading
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


logger = logging.getLogger(__name__)


class DuplicateUploadError(Exception):
    pass


@dataclass(slots=True)
class UploadMetadata:
    file_id: str
    filename: str
    stored_filename: str
    storage_path: str
    file_hash: str
    size_bytes: int
    content_type: str | None
    uploaded_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class FileStorage:
    def __init__(self, base_directory: str | Path = "uploads/resumes") -> None:
        self.base_directory = Path(base_directory)
        self.base_directory.mkdir(parents=True, exist_ok=True)
        self.index_path = self.base_directory / ".upload_index.json"
        self._lock = threading.Lock()
        self._index = self._load_index()

    def store(self, filename: str, content: bytes, content_type: str | None = None) -> UploadMetadata:
        file_hash = self._calculate_hash(content)

        with self._lock:
            existing = self._index.get(file_hash)
            if existing:
                logger.info("Duplicate upload blocked for filename=%s hash=%s", filename, file_hash)
                raise DuplicateUploadError("A resume with the same content has already been uploaded.")

            file_id = str(uuid4())
            safe_name = Path(filename).name
            stored_filename = f"{file_id}_{safe_name}"
            storage_path = self.base_directory / stored_filename
            storage_path.write_bytes(content)

            metadata = UploadMetadata(
                file_id=file_id,
                filename=safe_name,
                stored_filename=stored_filename,
                storage_path=str(storage_path),
                file_hash=file_hash,
                size_bytes=len(content),
                content_type=content_type,
            )

            self._index[file_hash] = asdict(metadata)
            self._persist_index()

        logger.info("Resume stored successfully file_id=%s path=%s", metadata.file_id, metadata.storage_path)
        return metadata

    def _calculate_hash(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def _load_index(self) -> dict[str, dict]:
        if not self.index_path.exists():
            return {}

        try:
            return json.loads(self.index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.warning("Upload index file was unreadable; starting with an empty index.")
            return {}

    def _persist_index(self) -> None:
        self.index_path.write_text(json.dumps(self._index, indent=2), encoding="utf-8")
