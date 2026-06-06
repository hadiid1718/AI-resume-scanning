from __future__ import annotations

from backend.app.services.jd_service import JDService


def test_parses_sectioned_job_description_into_structured_requirements() -> None:
    job_description = """
    Required Qualifications
    - Python
    - FastAPI
    - PostgreSQL
    - 3+ years of experience in backend development
    - Bachelor's degree in Computer Science

    Preferred Qualifications
    - Docker
    - Kubernetes
    - AWS
    - Master's degree is a plus
    """

    service = JDService()
    result = service.parse("Backend Engineer", job_description)

    assert result["required_skills"] == ["FastAPI", "PostgreSQL", "Python"]
    assert result["preferred_skills"] == ["AWS", "Docker", "Kubernetes"]
    assert result["experience_required"] == "3+ years"
    assert "Bachelor's degree in Computer Science" in result["education_requirements"][0]
    assert result["must_have"]["skills"] == ["FastAPI", "PostgreSQL", "Python"]
    assert result["nice_to_have"]["skills"] == ["AWS", "Docker", "Kubernetes"]


def test_parses_freeform_job_description_without_sections() -> None:
    job_description = """
    We are looking for a Data Engineer with strong Python, SQL, and Airflow skills.
    Must have 5 years of experience in data platforms and a Bachelor's degree.
    Nice to have: AWS, Docker, and dbt.
    """

    service = JDService()
    result = service.parse("Data Engineer", job_description)

    assert "Python" in result["required_skills"]
    assert "SQL" in result["required_skills"]
    assert result["experience_required"] == "5+ years"
    assert any("Bachelor" in item for item in result["education_requirements"])
    assert "AWS" in result["preferred_skills"]
    assert "Docker" in result["preferred_skills"]


def test_returns_structured_json_payload() -> None:
    job_description = """
    Qualifications:
    Python, FastAPI, and CI/CD experience
    Preferred: React
    Education: Bachelor's degree
    """

    service = JDService()
    result = service.parse("Full Stack Engineer", job_description)

    assert set(result.keys()) >= {
        "title",
        "description",
        "required_skills",
        "preferred_skills",
        "experience_required",
        "education_requirements",
        "must_have",
        "nice_to_have",
        "sections",
    }
    assert isinstance(result["must_have"], dict)
    assert isinstance(result["nice_to_have"], dict)
    assert isinstance(result["sections"], dict)
