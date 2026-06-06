from pydantic import BaseModel, Field


class ResumeUploadResponse(BaseModel):
    filename: str
    storage_path: str
    content_type: str | None = None
    size_bytes: int = Field(default=0, ge=0)


class ResumeTextRequest(BaseModel):
    resume_text: str = Field(min_length=1)


class ParsedResumeResponse(BaseModel):
    raw_text: str
    normalized_text: str
    word_count: int


class CandidateInfoResponse(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    summary: str | None = None
