from __future__ import annotations

import logging

from backend.app.modules.skill_extractor import SkillExtractor


logger = logging.getLogger(__name__)


class SkillService:
    def __init__(self, extractor: SkillExtractor | None = None) -> None:
        self.extractor = extractor or SkillExtractor()

    def extract(self, text: str) -> dict:
        logger.debug("Running skill extraction on resume text")
        extracted = self.extractor.extract(text)
        return {
            "skills": extracted["skills"],
            "categorized_skills": extracted["categorized_skills"],
            "confidence_scores": extracted["confidence_scores"],
            "all_matches": extracted["all_matches"],
        }
