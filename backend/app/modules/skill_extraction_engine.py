from backend.app.services.skill_service import SkillService


class SkillExtractionEngine:
    def __init__(self) -> None:
        self.service = SkillService()

    def extract(self, text: str) -> dict:
        extracted = self.service.extract(text)
        return {
            "skills": extracted["skills"],
            "keyword_terms": extracted["skills"],
            "categorized_skills": extracted["categorized_skills"],
            "confidence_scores": extracted["confidence_scores"],
            "all_matches": extracted["all_matches"],
        }

