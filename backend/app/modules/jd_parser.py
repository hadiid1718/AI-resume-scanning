from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

import spacy

from backend.app.services.skill_service import SkillService


logger = logging.getLogger(__name__)


SECTION_ALIASES = {
    "required": {"required", "requirements", "must have", "must-have", "essential", "qualifications", "required qualifications", "must have qualifications", "must-haves"},
    "preferred": {"preferred", "preferred qualifications", "nice to have", "nice-to-have", "bonus", "plus", "desired", "good to have"},
    "experience": {"experience", "experience required", "years of experience", "work experience"},
    "education": {"education", "education requirements", "education required", "degree", "qualifications"},
}

SKILL_SPLIT_PATTERN = re.compile(r"\s*(?:,|/|\band\b|\bor\b|;|\+|\|)\s*", re.IGNORECASE)
YEARS_PATTERN = re.compile(
    r"(?:(?P<min>\d{1,2})\+?\s*\+?\s*(?:years?|yrs?)|(?P<range_min>\d{1,2})\s*(?:-|to)\s*(?P<range_max>\d{1,2})\s*(?:years?|yrs?))",
    re.IGNORECASE,
)
EXPERIENCE_CONTEXT_PATTERN = re.compile(r"\b(\d{1,2}\+?\s*(?:years?|yrs?)\b|\d{1,2}\s*(?:-|to)\s*\d{1,2}\s*(?:years?|yrs?)\b)", re.IGNORECASE)
DEGREE_PATTERN = re.compile(
    r"\b(bachelor(?:'s)?|master(?:'s)?|mba|ph\.?d|doctor(?:ate)?|associate(?:'s)?|b\.?(?:\s*)sc|m\.?(?:\s*)sc|b\.?(?:\s*)a|m\.?(?:\s*)a|btech|mtech|bs|ms|ba|ma)\b",
    re.IGNORECASE,
)
EDUCATION_CONTEXT_PATTERN = re.compile(
    r"\b(bachelor|master|ph\.?d|doctor|associate|degree|diploma|certification|education|graduate)\b",
    re.IGNORECASE,
)
SKILL_CLEAN_PATTERN = re.compile(r"[^A-Za-z0-9+.#\- ]+")


@dataclass(slots=True)
class JobRequirementResult:
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    experience_required: str | None = None
    education_requirements: list[str] = field(default_factory=list)
    must_have: dict = field(default_factory=dict)
    nice_to_have: dict = field(default_factory=dict)
    sections: dict[str, list[str]] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "required_skills": self.required_skills,
            "preferred_skills": self.preferred_skills,
            "experience_required": self.experience_required,
            "education_requirements": self.education_requirements,
            "must_have": self.must_have,
            "nice_to_have": self.nice_to_have,
            "sections": self.sections,
        }


class JDParser:
    def __init__(self) -> None:
        self.nlp = spacy.blank("en")
        if "sentencizer" not in self.nlp.pipe_names:
            self.nlp.add_pipe("sentencizer")
        self.skill_service = SkillService()

    def parse(self, title: str, description: str) -> dict:
        normalized_text = self._normalize_text(description)
        lines = self._meaningful_lines(normalized_text)
        doc = self.nlp(normalized_text)

        sections = self._segment_sections(lines)
        required_skills = self._extract_skills(sections.get("required", []) + sections.get("experience", []) + sections.get("education", []))
        preferred_skills = self._extract_skills(sections.get("preferred", []))

        if not required_skills and not preferred_skills:
            inferred_required, inferred_preferred = self._extract_skills_by_context(lines)
            required_skills = inferred_required
            preferred_skills = inferred_preferred

        experience_required = self._extract_experience_requirement(lines)
        education_requirements = self._extract_education_requirements(sections.get("education", []) or lines)

        must_have_skills = sorted(self._unique(required_skills))
        nice_to_have_skills = sorted(self._unique(preferred_skills))

        result = JobRequirementResult(
            required_skills=must_have_skills,
            preferred_skills=nice_to_have_skills,
            experience_required=experience_required,
            education_requirements=education_requirements,
            must_have={
                "skills": must_have_skills,
                "experience": experience_required,
                "education": education_requirements,
            },
            nice_to_have={
                "skills": nice_to_have_skills,
            },
            sections=sections,
        )

        combined_skills = sorted(self._unique(must_have_skills + nice_to_have_skills))
        requirements: list[str] = list(education_requirements)
        if experience_required:
            requirements.append(experience_required)

        return {
            "title": title,
            "description": description,
            "skills": combined_skills,
            "requirements": requirements,
            **result.as_dict(),
        }

    def _segment_sections(self, lines: list[str]) -> dict[str, list[str]]:
        sections = {"required": [], "preferred": [], "experience": [], "education": [], "other": []}
        current_key = "other"

        for line in lines:
            lowered = line.lower().strip(" :-\t")
            next_key = self._match_section_heading(lowered)
            if next_key:
                current_key = next_key
                continue

            sections.setdefault(current_key, []).append(line)

        return sections

    def _match_section_heading(self, line: str) -> str | None:
        for key, aliases in SECTION_ALIASES.items():
            if line in aliases:
                return key
        return None

    def _extract_skills(self, lines: list[str]) -> list[str]:
        text = "\n".join(line for line in lines if line and not self._looks_like_experience_or_education(line))
        extracted = self.skill_service.extract(text)
        return self._unique(extracted["skills"])

    def _extract_skills_by_context(self, lines: list[str]) -> tuple[list[str], list[str]]:
        required: list[str] = []
        preferred: list[str] = []

        for line in lines:
            lowered = line.lower()
            bucket = "required"
            if any(alias in lowered for alias in SECTION_ALIASES["preferred"]):
                bucket = "preferred"
            elif any(alias in lowered for alias in SECTION_ALIASES["required"]):
                bucket = "required"

            extracted = self._extract_skills([line])
            if bucket == "preferred":
                preferred.extend(extracted)
            else:
                required.extend(extracted)

        return self._unique(required), self._unique(preferred)

    def _extract_experience_requirement(self, lines: list[str]) -> str | None:
        for line in lines:
            match = YEARS_PATTERN.search(line)
            if match:
                if match.group("min"):
                    return f"{match.group('min')}+ years"
                if match.group("range_min") and match.group("range_max"):
                    return f"{match.group('range_min')}-{match.group('range_max')} years"

        for sentence in doc_to_sentences(self.nlp, "\n".join(lines)):
            match = YEARS_PATTERN.search(sentence)
            if match:
                if match.group("min"):
                    return f"{match.group('min')}+ years"
                if match.group("range_min") and match.group("range_max"):
                    return f"{match.group('range_min')}-{match.group('range_max')} years"

        return None

    def _extract_education_requirements(self, lines: list[str]) -> list[str]:
        requirements: list[str] = []
        for line in lines:
            cleaned = self._clean_line(line)
            if not cleaned:
                continue
            if EDUCATION_CONTEXT_PATTERN.search(cleaned) or DEGREE_PATTERN.search(cleaned):
                requirements.append(self._normalize_education(cleaned))
        return self._unique(requirements)

    def _looks_like_experience_or_education(self, line: str) -> bool:
        return bool(EXPERIENCE_CONTEXT_PATTERN.search(line) or EDUCATION_CONTEXT_PATTERN.search(line))

    def _normalize_education(self, value: str) -> str:
        cleaned = self._clean_line(value)
        return cleaned

    def _normalize_text(self, text: str) -> str:
        return text.replace("\r\n", "\n").replace("\r", "\n")

    def _meaningful_lines(self, text: str) -> list[str]:
        lines: list[str] = []
        for raw_line in text.split("\n"):
            cleaned = self._clean_line(raw_line)
            if cleaned:
                lines.append(cleaned)
        return lines

    def _clean_line(self, value: str) -> str:
        return " ".join(value.split()).strip()

    def _unique(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        unique_values: list[str] = []
        for value in values:
            normalized_key = value.lower()
            if value and normalized_key not in seen:
                seen.add(normalized_key)
                unique_values.append(value)
        return unique_values


def doc_to_sentences(nlp, text: str) -> list[str]:
    doc = nlp(text)
    return [sentence.text.strip() for sentence in doc.sents if sentence.text.strip()]
