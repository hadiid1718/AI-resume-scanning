from __future__ import annotations

from backend.app.modules.skill_service import SkillService


def test_extracts_and_normalizes_skills_across_categories() -> None:
    text = """
    Python, PY, fastapi, FastAPI, Streamlit, React, PostgreSQL, postgres,
    AWS, Amazon Web Services, Docker, Kubernetes, Jenkins, GitHub, Git
    """

    service = SkillService()
    result = service.extract(text)

    assert result["skills"] == [
        "AWS",
        "Docker",
        "FastAPI",
        "Git",
        "GitHub",
        "Jenkins",
        "Kubernetes",
        "PostgreSQL",
        "Python",
        "React",
        "SQL",
        "Streamlit",
    ]
    assert result["categorized_skills"]["programming_languages"][0]["name"] == "Python"
    assert result["categorized_skills"]["frameworks"][0]["name"] == "FastAPI"
    assert result["categorized_skills"]["cloud_technologies"][0]["name"] == "AWS"
    assert result["confidence_scores"]["frameworks"] > 0


def test_returns_confidence_for_multiple_categories() -> None:
    text = "JavaScript, TypeScript, Node.js, MySQL, Azure, Terraform, CI/CD"

    service = SkillService()
    result = service.extract(text)

    assert set(result["confidence_scores"].keys()) == {
        "programming_languages",
        "frameworks",
        "databases",
        "cloud_technologies",
        "devops_tools",
    }
    assert result["confidence_scores"]["programming_languages"] > 0
    assert result["confidence_scores"]["cloud_technologies"] > 0
    assert result["confidence_scores"]["devops_tools"] > 0


def test_handles_resume_text_without_skills() -> None:
    text = "Experienced professional with strong communication and leadership skills."

    service = SkillService()
    result = service.extract(text)

    assert result["skills"] == []
    assert all(score == 0.0 for score in result["confidence_scores"].values())
