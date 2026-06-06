from backend.app.core.config import get_settings
from backend.app.modules.ai_evaluation_engine import AIEvaluationEngine
from backend.app.modules.candidate_information_extractor import CandidateInformationExtractor
from backend.app.modules.database_layer import DatabaseLayer
from backend.app.modules.job_description_parser import JobDescriptionParser
from backend.app.modules.matching_engine import MatchingEngine
from backend.app.modules.ranking_engine import RankingEngine
from backend.app.modules.report_generator import ReportGenerator
from backend.app.modules.resume_parser import ResumeParserModule
from backend.app.modules.resume_upload import ResumeUploadModule
from backend.app.modules.skill_extraction_engine import SkillExtractionEngine


class ResumeAnalysisPipeline:
    def __init__(self, database_layer: DatabaseLayer | None = None) -> None:
        settings = get_settings()
        self.upload_module = ResumeUploadModule(settings.upload_dir)
        self.resume_parser = ResumeParserModule()
        self.candidate_extractor = CandidateInformationExtractor()
        self.skill_engine = SkillExtractionEngine()
        self.job_parser = JobDescriptionParser()
        self.matching_engine = MatchingEngine()
        self.ranking_engine = RankingEngine()
        self.evaluation_engine = AIEvaluationEngine()
        self.report_generator = ReportGenerator(settings.report_dir)
        self.database_layer = database_layer

    def analyze(self, resume_text: str, job_title: str, job_description: str) -> dict:
        parsed_resume = self.resume_parser.parse_text(resume_text)
        candidate = self.candidate_extractor.extract(parsed_resume)
        candidate.update(self.skill_engine.extract(resume_text))

        job = self.job_parser.parse(job_title, job_description)
        match_result = self.matching_engine.match(candidate, job)
        rank_result = self.ranking_engine.rank(match_result)
        evaluation = self.evaluation_engine.evaluate(candidate, job, match_result)

        report = self.report_generator.build(
            {
                "candidate": candidate,
                "job": job,
                "match_result": match_result,
                "rank_result": rank_result,
                "evaluation": evaluation,
            }
        )

        payload = {
            "parsed_resume": parsed_resume,
            "candidate": candidate,
            "job": job,
            "match_result": match_result,
            "rank_result": rank_result,
            "evaluation": evaluation,
            "report": report,
        }

        if self.database_layer:
            self.database_layer.save_candidate_profile(candidate)
            self.database_layer.save_job_description(job)
            self.database_layer.save_match_record(
                {
                    "candidate_name": candidate.get("full_name"),
                    "job_title": job.get("title"),
                    "score": match_result.get("score", 0.0),
                    "breakdown": match_result,
                }
            )
            self.database_layer.save_report_record(
                {
                    "title": report["title"],
                    "markdown": report["markdown"],
                    "payload": payload,
                }
            )

        return payload
