from __future__ import annotations

from backend.app.services.education_service import EducationService


def test_detects_education_section_and_extracts_core_fields() -> None:
    resume_text = """
    Education
    Bachelor of Science in Computer Science
    Stanford University
    2018
    GPA: 3.8/4.0

    Experience
    Software Engineer at Acme Corp
    """

    service = EducationService()
    result = service.extract(resume_text)

    assert result["section_count"] == 1
    assert len(result["educations"]) == 1
    entry = result["educations"][0]
    assert entry["degree_name"] == "Bachelor of Science in Computer Science"
    assert entry["university_name"] == "Stanford University"
    assert entry["graduation_year"] == 2018
    assert entry["gpa"] == 3.8


def test_extracts_multiple_education_entries_from_different_formats() -> None:
    resume_text = """
    Academic Background
    M.Sc. Data Science | University of Oxford | 2021 | CGPA: 3.9

    Bachelor of Technology in Information Technology
    Indian Institute of Technology Delhi
    Graduated 2019
    GPA 3.6
    """

    service = EducationService()
    result = service.extract(resume_text)

    assert len(result["educations"]) == 2
    assert result["educations"][0]["degree_name"] == "Master of Science"
    assert result["educations"][0]["university_name"] == "University of Oxford"
    assert result["educations"][0]["graduation_year"] == 2021
    assert result["educations"][0]["gpa"] == 3.9
    assert result["educations"][1]["degree_name"] == "Bachelor of Technology"
    assert result["educations"][1]["university_name"] == "Indian Institute of Technology Delhi"
    assert result["educations"][1]["graduation_year"] == 2019
    assert result["educations"][1]["gpa"] == 3.6


def test_returns_structured_json_with_missing_optional_fields() -> None:
    resume_text = """
    Education
    Bachelor of Arts in English Literature
    University of Delhi
    """

    service = EducationService()
    result = service.extract(resume_text)

    assert isinstance(result["educations"], list)
    entry = result["educations"][0]
    assert entry["degree_name"] == "Bachelor of Arts in English Literature"
    assert entry["university_name"] == "University of Delhi"
    assert entry["graduation_year"] is None
    assert entry["gpa"] is None
