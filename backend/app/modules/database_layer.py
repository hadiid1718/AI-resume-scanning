from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.app.db.models import (
    CandidateEvaluation,
    CandidateProfile,
    JobDescription,
    MatchRecord,
    ReportRecord,
    ResumeUpload,
)


class DatabaseLayer:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save_resume_upload(self, payload: dict) -> ResumeUpload:
        record = ResumeUpload(**payload)
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def save_candidate_profile(self, payload: dict) -> CandidateProfile:
        record = CandidateProfile(**payload)
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def save_job_description(self, payload: dict) -> JobDescription:
        record = JobDescription(**payload)
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def save_match_record(self, payload: dict) -> MatchRecord:
        record = MatchRecord(**payload)
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def save_report_record(self, payload: dict) -> ReportRecord:
        record = ReportRecord(**payload)
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def save_evaluation(self, payload: dict) -> CandidateEvaluation:
        record = CandidateEvaluation(**payload)
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def list_evaluations(self, limit: int = 100) -> list[CandidateEvaluation]:
        return (
            self.session.query(CandidateEvaluation)
            .order_by(desc(CandidateEvaluation.ai_score), desc(CandidateEvaluation.created_at))
            .limit(limit)
            .all()
        )

    def get_rankings(self, limit: int = 100) -> list[dict]:
        rows = self.list_evaluations(limit=limit)
        rankings = []
        for rank, row in enumerate(rows, start=1):
            skills = row.skills or []
            if isinstance(skills, dict):
                skills = list(skills.values())
            rankings.append(
                {
                    "rank": rank,
                    "id": row.id,
                    "candidate_name": row.candidate_name,
                    "job_title": row.job_title,
                    "ai_score": row.ai_score,
                    "recommendation": row.recommendation,
                    "key_skills": skills[:8] if isinstance(skills, list) else [],
                    "experience_summary": row.experience_summary,
                    "payload": row.payload,
                }
            )
        return rankings

    def get_evaluation(self, evaluation_id: int) -> CandidateEvaluation | None:
        return self.session.get(CandidateEvaluation, evaluation_id)
