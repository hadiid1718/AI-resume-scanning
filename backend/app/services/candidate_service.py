from __future__ import annotations

import logging

from backend.app.modules.candidate_information.extractor import CandidateInformationExtractor


logger = logging.getLogger(__name__)


class CandidateInformationService:
    def __init__(self, extractor: CandidateInformationExtractor | None = None) -> None:
        self.extractor = extractor or CandidateInformationExtractor()

    def extract(self, parsed_resume: dict | str) -> dict[str, str | None]:
        if isinstance(parsed_resume, str):
            logger.debug("Candidate extraction received raw string input")
            return self.extractor.extract_from_text(parsed_resume)

        logger.debug("Candidate extraction received parsed resume input")
        return self.extractor.extract(parsed_resume)
