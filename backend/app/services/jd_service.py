from __future__ import annotations

import logging

from backend.app.modules.jd_parser import JDParser


logger = logging.getLogger(__name__)


class JDService:
    def __init__(self, parser: JDParser | None = None) -> None:
        self.parser = parser or JDParser()

    def parse(self, title: str, description: str) -> dict:
        logger.debug("Running job description parsing")
        return self.parser.parse(title, description)
