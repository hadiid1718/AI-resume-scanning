from __future__ import annotations

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from backend.app.modules.file_storage import DuplicateUploadError
from backend.app.modules.file_validator import FileValidationError
from backend.app.modules.upload_service import UploadService
from backend.app.schemas.resume import ResumeUploadResponse


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/resumes", tags=["resume-upload"])
upload_service = UploadService()


@router.post("/upload", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(file: UploadFile = File(...)) -> ResumeUploadResponse:
    try:
        content = await file.read()
        metadata = upload_service.upload_resume(
            filename=file.filename,
            content=content,
            content_type=file.content_type,
        )
        return ResumeUploadResponse.model_validate(metadata)
    except FileValidationError as exc:
        logger.warning("Resume validation failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except DuplicateUploadError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
