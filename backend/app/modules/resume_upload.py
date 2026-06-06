from pathlib import Path


class ResumeUploadModule:
    def __init__(self, upload_dir: str) -> None:
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save(self, filename: str, content: bytes, content_type: str | None = None) -> dict:
        target_path = self.upload_dir / filename
        target_path.write_bytes(content)
        return {
            "filename": filename,
            "storage_path": str(target_path),
            "content_type": content_type,
            "size_bytes": len(content),
        }
