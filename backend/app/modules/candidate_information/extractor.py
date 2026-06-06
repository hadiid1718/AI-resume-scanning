from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import spacy

from backend.app.modules.candidate_information.patterns import (
    EMAIL_PATTERN,
    GITHUB_PATTERN,
    LINKEDIN_PATTERN,
    LOCATION_LABEL_PATTERN,
    NAME_LABEL_PATTERN,
    PHONE_PATTERN,
    SECTION_STOPWORDS,
)


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CandidateExtractionResult:
    full_name: str | None
    email: str | None
    phone_number: str | None
    linkedin_url: str | None
    github_url: str | None
    location: str | None

    def as_dict(self) -> dict[str, str | None]:
        return {
            "full_name": self.full_name,
            "email": self.email,
            "phone_number": self.phone_number,
            "linkedin_url": self.linkedin_url,
            "github_url": self.github_url,
            "location": self.location,
        }


class CandidateInformationExtractor:
    def __init__(self) -> None:
        self.nlp = spacy.blank("en")
        if "sentencizer" not in self.nlp.pipe_names:
            self.nlp.add_pipe("sentencizer")

    def extract(self, parsed_resume: dict) -> dict[str, str | None]:
        text = parsed_resume.get("normalized_text") or parsed_resume.get("raw_text") or ""
        return self.extract_from_text(text)

    def extract_from_text(self, text: str) -> dict[str, str | None]:
        cleaned_text = self._normalize_text(text)
        lines = self._get_meaningful_lines(cleaned_text)
        doc = self.nlp(cleaned_text)

        result = CandidateExtractionResult(
            full_name=self._extract_full_name(lines, cleaned_text, doc),
            email=self._first_match(EMAIL_PATTERN, cleaned_text),
            phone_number=self._first_match(PHONE_PATTERN, cleaned_text),
            linkedin_url=self._first_match(LINKEDIN_PATTERN, cleaned_text),
            github_url=self._first_match(GITHUB_PATTERN, cleaned_text),
            location=self._extract_location(lines, cleaned_text),
        )

        return result.as_dict()

    def _extract_full_name(self, lines: list[str], cleaned_text: str, doc: spacy.tokens.Doc) -> str | None:
        labeled_name = self._extract_labeled_value(NAME_LABEL_PATTERN, cleaned_text)
        if labeled_name:
            return labeled_name

        contact_block = self._contact_block_end(lines)
        candidate_lines = [line for line in lines[:contact_block] if not self._looks_like_contact_line(line)]

        for line in candidate_lines:
            if self._looks_like_name(line):
                return line

        for sent in doc.sents:
            sentence = sent.text.strip()
            if self._looks_like_name(sentence):
                return sentence

        return candidate_lines[0] if candidate_lines else None

    def _extract_location(self, lines: list[str], cleaned_text: str) -> str | None:
        labeled_location = self._extract_labeled_value(LOCATION_LABEL_PATTERN, cleaned_text)
        if labeled_location:
            return labeled_location

        candidate_lines = [line for line in lines if not self._looks_like_contact_line(line)]
        for index, line in enumerate(candidate_lines):
            lowered = line.lower()
            if any(keyword in lowered for keyword in ("remote", "hybrid")):
                return line

            if self._looks_like_location(line):
                return line

            if index > 0 and not self._looks_like_name(line) and len(line.split()) <= 6:
                if any(char.isalpha() for char in line):
                    return line

        return None

    def _looks_like_name(self, value: str) -> bool:
        stripped = value.strip()
        if not stripped:
            return False

        if any(marker in stripped.lower() for marker in SECTION_STOPWORDS):
            return False

        if any(pattern.search(stripped) for pattern in (EMAIL_PATTERN, PHONE_PATTERN, LINKEDIN_PATTERN, GITHUB_PATTERN)):
            return False

        tokenized = [token for token in re.split(r"\s+", stripped) if token]
        if not 2 <= len(tokenized) <= 4:
            return False

        title_case_count = sum(1 for token in tokenized if token[:1].isupper() and token[1:].islower())
        return title_case_count >= max(2, len(tokenized) - 1)

    def _looks_like_location(self, value: str) -> bool:
        lowered = value.lower()
        location_keywords = {
            "city",
            "state",
            "province",
            "country",
            "remote",
            "hybrid",
            "usa",
            "uk",
            "india",
            "canada",
            "germany",
            "pakistan",
            "bangladesh",
            "europe",
            "asia",
        }
        return any(keyword in lowered for keyword in location_keywords) or "," in value

    def _looks_like_contact_line(self, value: str) -> bool:
        return bool(
            EMAIL_PATTERN.search(value)
            or PHONE_PATTERN.search(value)
            or LINKEDIN_PATTERN.search(value)
            or GITHUB_PATTERN.search(value)
        )

    def _extract_labeled_value(self, pattern: re.Pattern[str], text: str) -> str | None:
        match = pattern.search(text)
        if not match:
            return None
        return self._clean_value(match.group(1))

    def _first_match(self, pattern: re.Pattern[str], text: str) -> str | None:
        match = pattern.search(text)
        return self._clean_value(match.group(0)) if match else None

    def _clean_value(self, value: str) -> str:
        return " ".join(value.split()).strip("-:|, ")

    def _normalize_text(self, text: str) -> str:
        return text.replace("\r\n", "\n").replace("\r", "\n")

    def _get_meaningful_lines(self, text: str) -> list[str]:
        lines: list[str] = []
        for raw_line in text.split("\n"):
            line = " ".join(raw_line.split())
            if line:
                lines.append(line)
        return lines

    def _contact_block_end(self, lines: list[str]) -> int:
        for index, line in enumerate(lines[:6]):
            if self._looks_like_contact_line(line):
                return min(index + 2, len(lines))
        return min(3, len(lines))
