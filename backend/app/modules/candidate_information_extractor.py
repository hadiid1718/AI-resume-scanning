import re


class CandidateInformationExtractor:
    email_pattern = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    phone_pattern = re.compile(r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{3}\)?[\s-]?)\d{3}[\s-]?\d{4}")

    def extract(self, parsed_resume: dict) -> dict:
        text = parsed_resume.get("normalized_text") or parsed_resume.get("raw_text") or ""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        full_name = lines[0] if lines else None
        email_match = self.email_pattern.search(text)
        phone_match = self.phone_pattern.search(text)

        return {
            "full_name": full_name,
            "email": email_match.group(0) if email_match else None,
            "phone": phone_match.group(0) if phone_match else None,
            "summary": " ".join(lines[:5]) if lines else None,
        }
