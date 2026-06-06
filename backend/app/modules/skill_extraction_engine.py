from collections import Counter


class SkillExtractionEngine:
    default_skills = {
        "python",
        "fastapi",
        "streamlit",
        "sql",
        "postgresql",
        "sqlalchemy",
        "pandas",
        "numpy",
        "machine learning",
        "nlp",
        "docker",
        "aws",
        "git",
        "rest api",
        "microservices",
    }

    def extract(self, text: str) -> dict:
        normalized = text.lower()
        matches = sorted({skill for skill in self.default_skills if skill in normalized})
        tokens = [token for token in normalized.replace("/", " ").split() if token]
        common_terms = [term for term, _ in Counter(tokens).most_common(20)]

        return {
            "skills": matches,
            "keyword_terms": common_terms,
        }
