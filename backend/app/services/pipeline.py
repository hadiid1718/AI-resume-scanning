from backend.app.core.config import get_settings
from backend.app.modules.ai_evaluation_engine import AIEvaluationEngine
from backend.app.modules.database_layer import DatabaseLayer
from backend.app.modules.matching_engine import MatchingEngine
from backend.app.modules.ranking_engine import RankingEngine
from backend.app.modules.recommendation import extract_ai_score, score_to_recommendation
from backend.app.modules.report_generator import ReportGenerator
from backend.app.modules.resume_parser import ResumeParserModule
from backend.app.modules.resume_upload import ResumeUploadModule
from backend.app.modules.skill_extraction_engine import SkillExtractionEngine
from backend.app.services.candidate_service import CandidateInformationService
from backend.app.services.jd_service import JDService
from backend.app.workflows.resume_graph import ResumeGraphWorkflow


class ResumeAnalysisPipeline:
    def __init__(self, database_layer: DatabaseLayer | None = None) -> None:
        settings = get_settings()
        self.upload_module = ResumeUploadModule(settings.upload_dir)
        self.resume_parser = ResumeParserModule()
        self.candidate_extractor = CandidateInformationService()
        self.skill_engine = SkillExtractionEngine()
        self.job_parser = JDService()
        self.matching_engine = MatchingEngine()
        self.ranking_engine = RankingEngine()
        self.evaluation_engine = AIEvaluationEngine()
        self.report_generator = ReportGenerator(settings.report_dir)
        self.database_layer = database_layer
        self.workflow = ResumeGraphWorkflow(self)

    def analyze(self, resume_text: str, job_title: str, job_description: str) -> dict:
        payload = self.workflow.run(resume_text, job_title, job_description)
        if self.database_layer:
            self._persist(payload)
        return payload

    def analyze_batch(
        self,
        resume_texts: list[str],
        job_title: str,
        job_description: str,
    ) -> dict:
        batch = self.workflow.run_batch(resume_texts, job_title, job_description)
        if self.database_layer:
            for result in batch.get("results", []):
                self._persist(result)
        return batch

    def _persist(self, payload: dict) -> None:
        candidate = payload.get("candidate", {})
        job = payload.get("job", {})
        match_result = payload.get("match_result", {})
        report = payload.get("report", {})
        ai_score = extract_ai_score(payload)
        recommendation = payload.get("recommendation") or score_to_recommendation(ai_score)

        self.database_layer.save_candidate_profile(
            {
                "full_name": candidate.get("full_name"),
                "email": candidate.get("email"),
                "phone": candidate.get("phone_number") or candidate.get("phone"),
                "experience_years": candidate.get("experience_years") or candidate.get("years_experience"),
                "skills": candidate.get("skills"),
                "summary": candidate.get("summary") or candidate.get("location"),
            }
        )
        self.database_layer.save_job_description(
            {
                "title": job.get("title"),
                "description": job.get("description"),
                "skills": job.get("skills"),
                "requirements": job.get("requirements"),
            }
        )
        self.database_layer.save_match_record(
            {
                "candidate_name": candidate.get("full_name"),
                "job_title": job.get("title"),
                "score": float(ai_score),
                "breakdown": {
                    **match_result,
                    "ai_score": ai_score,
                    "recommendation": recommendation,
                    "ai_evaluation": payload.get("ai_evaluation"),
                },
            }
        )
        self.database_layer.save_evaluation(
            {
                "candidate_name": candidate.get("full_name"),
                "job_title": job.get("title"),
                "ai_score": ai_score,
                "recommendation": recommendation,
                "skills": candidate.get("skills"),
                "experience_summary": (payload.get("evaluation") or {}).get("experience_analysis", ""),
                "payload": payload,
            }
        )
        self.database_layer.save_report_record(
            {
                "title": report.get("title", "Candidate Report"),
                "markdown": report.get("markdown", ""),
                "payload": payload,
            }
        )
