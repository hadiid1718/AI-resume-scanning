from __future__ import annotations

import logging

from backend.app.modules.experience_extractor import ExperienceExtractor


logger = logging.getLogger(__name__)


class ExperienceService:
    def __init__(self, extractor: ExperienceExtractor | None = None) -> None:
        self.extractor = extractor or ExperienceExtractor()

    def extract(self, text: str) -> dict:
        logger.debug("Running experience extraction")
        result = self.extractor.extract(text)
        return {
            "experience_sections": result["experience_sections"],
            "experiences": result["experiences"],
            "total_years_experience": result["total_years_experience"],
            "date_ranges": result["date_ranges"],
            "section_count": result["section_count"],
        }
