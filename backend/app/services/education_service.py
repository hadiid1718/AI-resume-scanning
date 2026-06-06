from __future__ import annotations

import logging

from backend.app.modules.education_extractor import EducationExtractor


logger = logging.getLogger(__name__)


class EducationService:
    def __init__(self, extractor: EducationExtractor | None = None) -> None:
        self.extractor = extractor or EducationExtractor()

    def extract(self, text: str) -> dict:
        logger.debug("Running education extraction")
        result = self.extractor.extract(text)
        return {
            "education_sections": result["education_sections"],
            "educations": result["educations"],
            "section_count": result["section_count"],
        }
