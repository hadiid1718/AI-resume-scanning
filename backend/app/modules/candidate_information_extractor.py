from backend.app.services.candidate_service import CandidateInformationService
from backend.app.modules.candidate_information.extractor import CandidateInformationExtractor as _CandidateInformationExtractor


class CandidateInformationExtractor:
    def __init__(self) -> None:
        self.service = CandidateInformationService(_CandidateInformationExtractor())

    def extract(self, parsed_resume: dict) -> dict:
        extracted = self.service.extract(parsed_resume)
        lines = [line.strip() for line in (parsed_resume.get("normalized_text") or parsed_resume.get("raw_text") or "").splitlines() if line.strip()]
        extracted["summary"] = " ".join(lines[:5]) if lines else None
        extracted["phone"] = extracted.pop("phone_number", None)
        return extracted

