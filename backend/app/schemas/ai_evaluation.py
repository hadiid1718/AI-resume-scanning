from pydantic import BaseModel

class AIEvaluationRequest(BaseModel):
    candidate: dict
    job: dict
    match_result: dict | None = None

class AIEvaluationResponse(BaseModel):
    score: int
    verdict: str
    overall_assessment: str
    candidate_name: str
    role: str
    company: str
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]

class AIBatchItem(BaseModel):
    candidate: dict
    job: dict
    match_result: dict | None = None

class AIBatchEvaluationRequest(BaseModel):
    candidates: list[AIBatchItem]

class AIBatchEvaluationResponse(BaseModel):
    evaluations: list[AIEvaluationResponse]
    total: int