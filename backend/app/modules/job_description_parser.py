from backend.app.modules.skill_extraction_engine import SkillExtractionEngine


class JobDescriptionParser:
    def __init__(self) -> None:
        self.skill_engine = SkillExtractionEngine()

    def parse(self, title: str, description: str) -> dict:
        skills = self.skill_engine.extract(description)
        lines = [line.strip("-• \t") for line in description.splitlines() if line.strip()]

        return {
            "title": title,
            "description": description,
            "skills": skills["skills"],
            "requirements": lines[:10],
        }
