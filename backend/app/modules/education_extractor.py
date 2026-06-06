from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import spacy


logger = logging.getLogger(__name__)


EDUCATION_SECTION_HEADINGS = {
    "education",
    "educational background",
    "academic background",
    "academics",
    "qualification",
    "qualifications",
}

SECTION_BREAKERS = {
    "experience",
    "work experience",
    "professional experience",
    "skills",
    "projects",
    "certifications",
    "summary",
    "profile",
    "contact",
}

DEGREE_PATTERNS = [
    re.compile(r"\b(b\.?(?:\s*)sc|bachelor(?:'s)?(?:\s+of)?(?:\s+[a-z]+)?|b\.?(?:\s*)a|master(?:'s)?(?:\s+of)?(?:\s+[a-z]+)?|m\.?(?:\s*)sc|m\.?(?:\s*)a|ph\.?(?:\s*)d|doctor(?:ate)?|associate(?:'s)?|mba|beng|meng|msc|bs|ba|ms|ma|btech|mtech)\b", re.IGNORECASE),
]
UNIVERSITY_PATTERN = re.compile(
    r"\b(?:university|college|institute|school|academy|polytechnic|institute of technology|technological university|national university)\b",
    re.IGNORECASE,
)
GPA_PATTERN = re.compile(
    r"\b(?:gpa|cgpa)\s*[:\-]?\s*(\d(?:\.\d{1,2})?)\s*(?:/\s*4(?:\.0)?)?\b",
    re.IGNORECASE,
)
YEAR_PATTERN = re.compile(r"\b(19\d{2}|20\d{2})\b")
PIPE_SPLIT_PATTERN = re.compile(r"\s*[|•·]\s*")


@dataclass(slots=True)
class EducationEntry:
    degree_name: str | None
    university_name: str | None
    graduation_year: int | None
    gpa: float | None
    raw_block: str
    confidence: float

    def to_dict(self) -> dict[str, str | int | float | None]:
        return {
            "degree_name": self.degree_name,
            "university_name": self.university_name,
            "graduation_year": self.graduation_year,
            "gpa": self.gpa,
            "raw_block": self.raw_block,
            "confidence": round(self.confidence, 2),
        }


class EducationExtractor:
    def __init__(self) -> None:
        self.nlp = spacy.blank("en")
        if "sentencizer" not in self.nlp.pipe_names:
            self.nlp.add_pipe("sentencizer")

    def extract(self, text: str) -> dict:
        normalized_text = self._normalize_text(text)
        lines = self._meaningful_lines(normalized_text)
        doc = self.nlp(normalized_text)

        education_sections = self._extract_education_sections(lines)
        entries: list[EducationEntry] = []

        for section in education_sections:
            entries.extend(self._extract_entries_from_section(section, doc))

        return {
            "education_sections": education_sections,
            "educations": [entry.to_dict() for entry in entries],
            "section_count": len(education_sections),
        }

    def _extract_education_sections(self, lines: list[str]) -> list[list[str]]:
        sections: list[list[str]] = []
        current: list[str] = []
        in_education = False

        for line in lines:
            lowered = line.lower().strip(" :-\t")
            if self._is_education_heading(lowered):
                if in_education and current:
                    sections.append(current)
                    current = []
                in_education = True
                continue

            if in_education:
                if self._is_section_breaker(lowered):
                    if current:
                        sections.append(current)
                    current = []
                    in_education = False
                    continue
                current.append(line)

        if in_education and current:
            sections.append(current)

        return [section for section in sections if any(self._looks_like_education_content(line) for line in section)]

    def _extract_entries_from_section(self, section_lines: list[str], doc: spacy.tokens.Doc) -> list[EducationEntry]:
        chunks = self._split_into_education_chunks(section_lines)
        entries: list[EducationEntry] = []

        for chunk in chunks:
            raw_block = "\n".join(chunk)
            degree_name = self._extract_degree_name(chunk, doc)
            university_name = self._extract_university_name(chunk, doc)
            graduation_year = self._extract_graduation_year(raw_block)
            gpa = self._extract_gpa(raw_block)
            confidence = self._calculate_confidence(degree_name, university_name, graduation_year, gpa)

            entries.append(
                EducationEntry(
                    degree_name=degree_name,
                    university_name=university_name,
                    graduation_year=graduation_year,
                    gpa=gpa,
                    raw_block=raw_block,
                    confidence=confidence,
                )
            )

        return entries

    def _split_into_education_chunks(self, section_lines: list[str]) -> list[list[str]]:
        if not section_lines:
            return []

        chunks: list[list[str]] = []
        current: list[str] = []

        for line in section_lines:
            if self._looks_like_degree_line(line) and self._chunk_has_education_signal(current):
                chunks.append(current)
                current = [line]
            else:
                current.append(line)

        if current:
            chunks.append(current)

        return [chunk for chunk in chunks if any(self._looks_like_education_content(line) for line in chunk)]

    def _extract_degree_name(self, chunk: list[str], doc: spacy.tokens.Doc) -> str | None:
        for line in chunk:
            degree = self._parse_degree_line(line)
            if degree:
                return degree

        for sent in doc.sents:
            degree = self._parse_degree_line(sent.text)
            if degree:
                return degree

        return None

    def _extract_university_name(self, chunk: list[str], doc: spacy.tokens.Doc) -> str | None:
        for line in chunk:
            university = self._parse_university_line(line)
            if university:
                return university

        for sent in doc.sents:
            university = self._parse_university_line(sent.text)
            if university:
                return university

        return None

    def _extract_graduation_year(self, text: str) -> int | None:
        matches = [int(match) for match in YEAR_PATTERN.findall(text)]
        if not matches:
            return None

        candidates = [year for year in matches if 1950 <= year <= 2035]
        if not candidates:
            return None

        return max(candidates)

    def _extract_gpa(self, text: str) -> float | None:
        match = GPA_PATTERN.search(text)
        if not match:
            return None

        try:
            return round(float(match.group(1)), 2)
        except ValueError:
            return None

    def _parse_degree_line(self, line: str) -> str | None:
        cleaned = self._clean_line(line)
        if not cleaned:
            return None

        match = DEGREE_PATTERNS[0].search(cleaned)
        if match:
            return self._normalize_degree_name(cleaned)

        if any(token in cleaned.lower() for token in ("bachelor", "master", "doctorate", "associate", "mba", "bsc", "msc", "btech", "mtech")):
            return self._normalize_degree_name(cleaned)

        return None

    def _parse_university_line(self, line: str) -> str | None:
        cleaned = self._clean_line(line)
        if not cleaned:
            return None

        for piece in [part.strip() for part in PIPE_SPLIT_PATTERN.split(cleaned) if part.strip()]:
            if UNIVERSITY_PATTERN.search(piece):
                return self._normalize_university_name(piece)

        if UNIVERSITY_PATTERN.search(cleaned):
            return self._normalize_university_name(cleaned)

        if any(marker in cleaned.lower() for marker in ("univ.", "inst.", "tech university", "college of", "school of")):
            return self._normalize_university_name(cleaned)

        return None

    def _looks_like_new_education_entry(self, line: str) -> bool:
        return bool(self._looks_like_degree_line(line))

    def _looks_like_degree_line(self, line: str) -> bool:
        return bool(self._parse_degree_line(line))

    def _chunk_has_education_signal(self, chunk: list[str]) -> bool:
        return any(
            self._parse_degree_line(line)
            or self._parse_university_line(line)
            or YEAR_PATTERN.search(line)
            or GPA_PATTERN.search(line)
            for line in chunk
        )

    def _looks_like_education_content(self, line: str) -> bool:
        lowered = line.lower().strip(" :-\t")
        return bool(
            self._parse_degree_line(line)
            or self._parse_university_line(line)
            or GPA_PATTERN.search(line)
            or YEAR_PATTERN.search(line)
            or any(keyword in lowered for keyword in ("thesis", "dissertation", "honors", "graduated", "major", "minor"))
        )

    def _is_education_heading(self, value: str) -> bool:
        normalized = self._clean_line(value).lower().strip(" :-")
        return normalized in EDUCATION_SECTION_HEADINGS

    def _is_section_breaker(self, value: str) -> bool:
        normalized = self._clean_line(value).lower().strip(" :-")
        return normalized in SECTION_BREAKERS

    def _calculate_confidence(
        self,
        degree_name: str | None,
        university_name: str | None,
        graduation_year: int | None,
        gpa: float | None,
    ) -> float:
        score = 0.2
        if degree_name:
            score += 0.3
        if university_name:
            score += 0.25
        if graduation_year:
            score += 0.15
        if gpa is not None:
            score += 0.1
        return min(1.0, score)

    def _normalize_text(self, text: str) -> str:
        return text.replace("\r\n", "\n").replace("\r", "\n")

    def _meaningful_lines(self, text: str) -> list[str]:
        lines: list[str] = []
        for raw_line in text.split("\n"):
            line = self._clean_line(raw_line)
            if line:
                lines.append(line)
        return lines

    def _clean_line(self, value: str) -> str:
        return " ".join(value.split()).strip()

    def _normalize_degree_name(self, value: str) -> str:
        cleaned = self._clean_line(value)
        replacements = {
            "b.sc": "Bachelor of Science",
            "bsc": "Bachelor of Science",
            "b.s": "Bachelor of Science",
            "b.a": "Bachelor of Arts",
            "ba": "Bachelor of Arts",
            "m.sc": "Master of Science",
            "msc": "Master of Science",
            "m.s": "Master of Science",
            "ms": "Master of Science",
            "m.a": "Master of Arts",
            "ma": "Master of Arts",
            "mba": "Master of Business Administration",
            "ph.d": "Doctor of Philosophy",
            "phd": "Doctor of Philosophy",
            "btech": "Bachelor of Technology",
            "mtech": "Master of Technology",
        }
        lowered = cleaned.lower()
        for raw, normalized in replacements.items():
            if re.search(rf"\b{re.escape(raw)}\b", lowered):
                return normalized

        if lowered.startswith("bachelor of technology"):
            return "Bachelor of Technology"
        if lowered.startswith("master of technology"):
            return "Master of Technology"

        return cleaned

    def _normalize_university_name(self, value: str) -> str:
        return self._clean_line(value)
