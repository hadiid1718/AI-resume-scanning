from __future__ import annotations

from backend.app.modules.experience_service import ExperienceService


def test_extracts_experience_sections_company_titles_and_total_years() -> None:
    resume_text = """
    Professional Experience
    Senior Software Engineer at Acme Corp
    Jan 2020 - Present
    Built internal APIs and automated workflows.

    Software Engineer | Beta Labs
    2017 - 2020
    Developed backend services.

    Education
    BSc Computer Science
    """

    service = ExperienceService()
    result = service.extract(resume_text)

    assert result["section_count"] == 1
    assert len(result["experiences"]) == 2
    assert result["experiences"][0]["company_name"] == "Acme Corp"
    assert result["experiences"][0]["job_title"] == "Senior Software Engineer"
    assert result["experiences"][1]["company_name"] == "Beta Labs"
    assert result["experiences"][1]["job_title"] == "Software Engineer"
    assert result["total_years_experience"] > 4


def test_merges_overlapping_date_ranges() -> None:
    resume_text = """
    Work Experience
    Backend Engineer at Delta Systems
    01/2019 - 06/2021
    Senior Backend Engineer at Delta Systems
    03/2021 - Present
    """

    service = ExperienceService()
    result = service.extract(resume_text)

    assert len(result["experiences"]) == 2
    assert len(result["date_ranges"]) == 1
    assert result["total_years_experience"] > 5


def test_handles_multiple_resume_formats_and_returns_structured_data() -> None:
    resume_text = """
    EXPERIENCE
    Full Stack Developer @ Nova Studio | London, UK | 2018 - 2020
    - Built web apps

    Lead Developer
    Orion Technologies
    2020 - Present
    """

    service = ExperienceService()
    result = service.extract(resume_text)

    assert isinstance(result["experiences"], list)
    assert result["experiences"][0]["company_name"] == "Nova Studio"
    assert result["experiences"][0]["job_title"] == "Full Stack Developer"
    assert result["experiences"][1]["company_name"] == "Orion Technologies"
    assert result["experiences"][1]["job_title"] == "Lead Developer"
    assert result["total_years_experience"] >= 4
