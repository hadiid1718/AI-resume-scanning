from sqlalchemy.orm import Session

from backend.app.db.models import CandidateProfile, JobDescription, MatchRecord, ReportRecord, ResumeUpload


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
