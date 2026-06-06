from pydantic import BaseModel, Field


class MatchRequest(BaseModel):
    candidate_skills: list[str] = Field(default_factory=list)
    job_skills: list[str] = Field(default_factory=list)


class MatchResponse(BaseModel):
    score: float
    overlap_skills: list[str]
    missing_skills: list[str]


class RankResponse(BaseModel):
    rank: str
    score: float


class EvaluationResponse(BaseModel):
    overall_assessment: str
    strengths: list[str]
    gaps: list[str]
    recommendations: list[str]


class ReportResponse(BaseModel):
    title: str
    report_path: str
    markdown: str
