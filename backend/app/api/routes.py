from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.core.database import get_db
from backend.app.modules.database_layer import DatabaseLayer
from backend.app.api.upload_routes import router as upload_router
from backend.app.schemas.job import JobDescriptionRequest, JobDescriptionResponse
from backend.app.schemas.match import EvaluationResponse, MatchRequest, MatchResponse, RankResponse, ReportResponse
from backend.app.schemas.resume import CandidateInfoResponse, ParsedResumeResponse, ResumeTextRequest
from backend.app.services.pipeline import ResumeAnalysisPipeline

from backend.app.schemas.ai_evaluation import AIEvaluationRequest, AIEvaluationResponse, AIBatchEvaluationRequest, AIBatchEvaluationResponse
from backend.app.services.ai_evaluator import AIEvaluationEngine

router = APIRouter(prefix="/api/v1", tags=["resume-scanning"])
router.include_router(upload_router)


def get_pipeline(db: Session = Depends(get_db)) -> ResumeAnalysisPipeline:
    return ResumeAnalysisPipeline(DatabaseLayer(db))


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {"status": "ok", "app_name": settings.app_name, "environment": settings.environment}


@router.post("/resumes/parse", response_model=ParsedResumeResponse)
def parse_resume(payload: ResumeTextRequest, pipeline: ResumeAnalysisPipeline = Depends(get_pipeline)) -> dict:
    return pipeline.resume_parser.parse_text(payload.resume_text)


@router.post("/candidates/extract", response_model=CandidateInfoResponse)
def extract_candidate(payload: ResumeTextRequest, pipeline: ResumeAnalysisPipeline = Depends(get_pipeline)) -> dict:
    parsed_resume = pipeline.resume_parser.parse_text(payload.resume_text)
    return pipeline.candidate_extractor.extract(parsed_resume)


@router.post("/skills/extract")
def extract_skills(payload: ResumeTextRequest, pipeline: ResumeAnalysisPipeline = Depends(get_pipeline)) -> dict:
    return pipeline.skill_engine.extract(payload.resume_text)


@router.post("/jobs/parse", response_model=JobDescriptionResponse)
def parse_job(payload: JobDescriptionRequest, pipeline: ResumeAnalysisPipeline = Depends(get_pipeline)) -> dict:
    return pipeline.job_parser.parse(payload.title, payload.description)


@router.post("/match", response_model=MatchResponse)
def match_resume(match_request: MatchRequest, pipeline: ResumeAnalysisPipeline = Depends(get_pipeline)) -> dict:
    candidate = {"skills": match_request.candidate_skills}
    job = {"skills": match_request.job_skills}
    return pipeline.matching_engine.match(candidate, job)


@router.post("/rank", response_model=RankResponse)
def rank_resume(match_response: MatchResponse, pipeline: ResumeAnalysisPipeline = Depends(get_pipeline)) -> dict:
    return pipeline.ranking_engine.rank(match_response.model_dump())


@router.post("/evaluate", response_model=EvaluationResponse)
def evaluate_resume(payload: dict, pipeline: ResumeAnalysisPipeline = Depends(get_pipeline)) -> dict:
    return pipeline.evaluation_engine.evaluate(payload.get("candidate", {}), payload.get("job", {}), payload.get("match_result", {}))


@router.post("/report", response_model=ReportResponse)
def generate_report(payload: dict, pipeline: ResumeAnalysisPipeline = Depends(get_pipeline)) -> dict:
    return pipeline.report_generator.build(payload)


@router.post("/analyze")
def analyze_resume(
    resume_text: str = Form(...),
    job_title: str = Form(...),
    job_description: str = Form(...),
    pipeline: ResumeAnalysisPipeline = Depends(get_pipeline),
) -> dict:
    return pipeline.analyze(resume_text=resume_text, job_title=job_title, job_description=job_description)



@router.post("/ai/evaluate", response_model=AIEvaluationResponse)
def ai_evaluate_resume(
    payload: AIEvaluationRequest,
    pipeline: ResumeAnalysisPipeline = Depends(get_pipeline),
) -> dict:
    return pipeline.ai_evaluation_engine.evaluate(
        candidate=payload.candidate,
        job=payload.job,
        match_result=payload.match_result,
    )


@router.post("/ai/evaluate/batch", response_model=AIBatchEvaluationResponse)
def ai_evaluate_batch(
    payload: AIBatchEvaluationRequest,
    db: Session = Depends(get_db),
) -> dict:
    engine = AIEvaluationEngine()
    results = [
        engine.evaluate(
            candidate=item.candidate,
            job=item.job,
            match_result=item.match_result,
        )
        for item in payload.candidates
    ]
    ranked = sorted(results, key=lambda r: r["score"], reverse=True)
    return {"evaluations": ranked, "total": len(ranked)}