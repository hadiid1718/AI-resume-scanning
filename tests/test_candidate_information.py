from __future__ import annotations

from backend.app.services.candidate_service import CandidateInformationService


def test_extracts_structured_contact_information_from_labeled_resume() -> None:
    text = """John Doe
Full Name: John Doe
Email: john.doe@example.com
Phone: +1 (555) 123-4567
LinkedIn: https://www.linkedin.com/in/johndoe/
GitHub: https://github.com/johndoe
Location: New York, NY
"""

    service = CandidateInformationService()
    result = service.extract(text)

    assert result["full_name"] == "John Doe"
    assert result["email"] == "john.doe@example.com"
    assert result["phone_number"] == "+1 (555) 123-4567"
    assert result["linkedin_url"] == "https://www.linkedin.com/in/johndoe/"
    assert result["github_url"] == "https://github.com/johndoe"
    assert result["location"] == "New York, NY"


def test_extracts_information_from_contact_block_resume() -> None:
    text = """Jane Marie Smith
Senior Data Analyst
jane.smith@company.io | +44 20 7946 0958
linkedin.com/in/janesmith
github.com/janesmith
London, UK
"""

    service = CandidateInformationService()
    result = service.extract(text)

    assert result["full_name"] == "Jane Marie Smith"
    assert result["email"] == "jane.smith@company.io"
    assert result["phone_number"] == "+44 20 7946 0958"
    assert result["linkedin_url"] == "linkedin.com/in/janesmith"
    assert result["github_url"] == "github.com/janesmith"
    assert result["location"] == "London, UK"


def test_returns_json_structure_with_missing_optional_fields() -> None:
    text = """Aman Khan
aman.khan@example.com
Dubai, UAE
"""

    service = CandidateInformationService()
    result = service.extract(text)

    assert set(result.keys()) == {"full_name", "email", "phone_number", "linkedin_url", "github_url", "location"}
    assert result["full_name"] == "Aman Khan"
    assert result["email"] == "aman.khan@example.com"
    assert result["phone_number"] is None
    assert result["linkedin_url"] is None
    assert result["github_url"] is None
    assert result["location"] == "Dubai, UAE"
