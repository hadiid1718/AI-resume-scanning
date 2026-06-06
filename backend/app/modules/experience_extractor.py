from __future__ import annotations

import logging
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date
from typing import Iterable

import spacy


logger = logging.getLogger(__name__)


MONTH_MAP = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

SECTION_HEADINGS = {
    "experience",
    "work experience",
    "professional experience",
    "employment history",
    "work history",
    "career history",
    "relevant experience",
}

DATE_RANGE_PATTERN = re.compile(
    r"(?P<start>(?:\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+\d{4})|(?:\b\d{1,2}[/-]\d{4})|(?:\b\d{4}[/-]\d{1,2})|(?:\b\d{4}))\s*(?:-|–|—|to)\s*(?P<end>(?:present|current|now)|(?:\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+\d{4})|(?:\b\d{1,2}[/-]\d{4})|(?:\b\d{4}[/-]\d{1,2})|(?:\b\d{4}))",
    re.IGNORECASE,
)
AT_PATTERN = re.compile(r"\b(?:at|@)\s+([A-Za-z0-9&.,()'\-/ ]{2,80})")
PIPE_SPLIT_PATTERN = re.compile(r"\s*[|•·]\s*")
TITLE_STOPWORDS = {
    "experience",
    "summary",
    "skills",
    "education",
    "projects",
    "certifications",
    "responsibilities",
    "achievements",
}
TITLE_HINTS = {
    "engineer",
    "developer",
    "analyst",
    "scientist",
    "manager",
    "consultant",
    "architect",
    "specialist",
    "lead",
    "director",
    "administrator",
    "designer",
    "tester",
    "intern",
    "officer",
    "coordinator",
    "executive",
    "head",
    "owner",
    "researcher",
}


@dataclass(slots=True)
class ExperiencePeriod:
    start: date
    end: date

    def to_dict(self) -> dict[str, str]:
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
        }


@dataclass(slots=True)
class ExperienceEntry:
    company_name: str | None
    job_title: str | None
    date_range: ExperiencePeriod | None
    raw_block: str
    confidence: float

    def to_dict(self) -> dict[str, str | float | dict[str, str] | None]:
        return {
            "company_name": self.company_name,
            "job_title": self.job_title,
            "date_range": self.date_range.to_dict() if self.date_range else None,
            "raw_block": self.raw_block,
            "confidence": round(self.confidence, 2),
        }


class ExperienceExtractor:
    def __init__(self) -> None:
        self.nlp = spacy.blank("en")
        if "sentencizer" not in self.nlp.pipe_names:
            self.nlp.add_pipe("sentencizer")

    def extract(self, text: str) -> dict:
        normalized_text = self._normalize_text(text)
        lines = self._meaningful_lines(normalized_text)
        doc = self.nlp(normalized_text)

        experience_sections = self._extract_experience_sections(lines)
        experiences: list[ExperienceEntry] = []
        all_periods: list[ExperiencePeriod] = []

        for section in experience_sections:
            extracted_entries = self._extract_entries_from_section(section, doc)
            experiences.extend(extracted_entries)
            all_periods.extend([entry.date_range for entry in extracted_entries if entry.date_range])

        merged_periods = self._merge_periods(all_periods)
        total_years = self._calculate_total_years(merged_periods)

        return {
            "experience_sections": experience_sections,
            "experiences": [entry.to_dict() for entry in experiences],
            "total_years_experience": round(total_years, 2),
            "date_ranges": [period.to_dict() for period in merged_periods],
            "section_count": len(experience_sections),
        }

    def _extract_experience_sections(self, lines: list[str]) -> list[list[str]]:
        sections: list[list[str]] = []
        current: list[str] = []
        in_experience = False

        for line in lines:
            lowered = line.lower().strip(" :\t-")
            if self._is_section_heading(lowered):
                if in_experience and current:
                    sections.append(current)
                    current = []
                in_experience = True
                continue

            if in_experience:
                if self._looks_like_new_section(line):
                    if current:
                        sections.append(current)
                    current = []
                    in_experience = False
                    continue
                current.append(line)

        if in_experience and current:
            sections.append(current)

        return [section for section in sections if any(self._looks_like_experience_content(line) for line in section)]

    def _extract_entries_from_section(self, section_lines: list[str], doc: spacy.tokens.Doc) -> list[ExperienceEntry]:
        chunks = self._split_into_experience_chunks(section_lines)
        entries: list[ExperienceEntry] = []

        for chunk in chunks:
            raw_block = "\n".join(chunk)
            date_range = self._extract_date_range(chunk[-1])
            title = self._extract_job_title(chunk, doc)
            company = self._extract_company_name(chunk, title)
            confidence = self._calculate_confidence(chunk, title, company, date_range)

            entries.append(
                ExperienceEntry(
                    company_name=company,
                    job_title=title,
                    date_range=date_range,
                    raw_block=raw_block,
                    confidence=confidence,
                )
            )

        return entries

    def _split_into_experience_chunks(self, section_lines: list[str]) -> list[list[str]]:
        date_indices = [index for index, line in enumerate(section_lines) if self._contains_date_range(line)]
        if not date_indices:
            return [section_lines] if any(self._looks_like_experience_content(line) for line in section_lines) else []

        chunks: list[list[str]] = []
        for index, date_index in enumerate(date_indices):
            start = max(0, date_index - 2)
            chunk = section_lines[start : date_index + 1]
            if any(self._looks_like_experience_content(line) for line in chunk):
                chunks.append(chunk)

        return chunks

    def _extract_job_title(self, chunk: list[str], doc: spacy.tokens.Doc) -> str | None:
        for line in reversed(chunk):
            title = self._parse_title_line(line)
            if title:
                return title

        for sent in doc.sents:
            sentence = sent.text.strip()
            if any(hint in sentence.lower() for hint in TITLE_HINTS):
                title = self._parse_title_line(sentence)
                if title:
                    return title

        return None

    def _extract_company_name(self, chunk: list[str], job_title: str | None) -> str | None:
        for line in reversed(chunk):
            company = self._parse_company_line(line, job_title)
            if company:
                return company

        return None

    def _parse_title_line(self, line: str) -> str | None:
        cleaned = self._clean_line(line)
        if not cleaned:
            return None

        if self._contains_date_range(cleaned) and not self._looks_like_composite_experience_line(cleaned):
            return None

        pieces = self._split_title_company_pieces(cleaned)
        for piece in pieces:
            if self._looks_like_title(piece):
                return piece

        if self._looks_like_title(cleaned):
            return cleaned

        if " at " in cleaned.lower():
            left, _right = re.split(r"\bat\b", cleaned, maxsplit=1, flags=re.IGNORECASE)
            if self._looks_like_title(left):
                return self._clean_line(left)

        return None

    def _parse_company_line(self, line: str, job_title: str | None) -> str | None:
        cleaned = self._clean_line(line)
        if not cleaned:
            return None

        if self._contains_date_range(cleaned) and not self._looks_like_composite_experience_line(cleaned):
            return None

        pieces = self._split_title_company_pieces(cleaned)
        if len(pieces) >= 2:
            for piece in pieces:
                if job_title and piece == job_title:
                    continue
                if self._looks_like_company(piece):
                    return piece

        at_match = AT_PATTERN.search(cleaned)
        if at_match:
            candidate = self._clean_line(at_match.group(1))
            if self._looks_like_company(candidate):
                return candidate

        if self._looks_like_company(cleaned) and not self._looks_like_title(cleaned):
            return cleaned

        return None

    def _split_title_company_pieces(self, cleaned: str) -> list[str]:
        pieces: list[str] = []
        for pipe_piece in PIPE_SPLIT_PATTERN.split(cleaned):
            pipe_piece = self._clean_line(pipe_piece)
            if not pipe_piece:
                continue

            if " at " in pipe_piece.lower():
                left, right = re.split(r"\bat\b", pipe_piece, maxsplit=1, flags=re.IGNORECASE)
                if self._clean_line(left):
                    pieces.append(self._clean_line(left))
                if self._clean_line(right):
                    pieces.append(self._clean_line(right))
                continue

            if " @ " in f" {pipe_piece.lower()} ":
                left, right = re.split(r"\@", pipe_piece, maxsplit=1)
                if self._clean_line(left):
                    pieces.append(self._clean_line(left))
                if self._clean_line(right):
                    pieces.append(self._clean_line(right))
                continue

            pieces.append(pipe_piece)

        return pieces

    def _extract_date_range(self, text: str) -> ExperiencePeriod | None:
        match = DATE_RANGE_PATTERN.search(text)
        if not match:
            return None

        start = self._parse_date_token(match.group("start"))
        end_token = match.group("end")
        end = self._parse_date_token(end_token, allow_present=True)
        if not start or not end:
            return None

        if end < start:
            start, end = end, start

        return ExperiencePeriod(start=start, end=end)

    def _parse_date_token(self, token: str | None, allow_present: bool = False) -> date | None:
        if not token:
            return None

        normalized = token.strip().lower().rstrip(".")
        if allow_present and normalized in {"present", "current", "now"}:
            return date.today()

        month_year = re.fullmatch(r"([a-z]+)\s+(\d{4})", normalized)
        if month_year:
            month = MONTH_MAP.get(month_year.group(1)[:3], MONTH_MAP.get(month_year.group(1)))
            if month:
                return date(int(month_year.group(2)), month, 1)

        month_year_numeric = re.fullmatch(r"(\d{1,2})[/-](\d{4})", normalized)
        if month_year_numeric:
            month = int(month_year_numeric.group(1))
            return date(int(month_year_numeric.group(2)), month, 1)

        year_month = re.fullmatch(r"(\d{4})[/-](\d{1,2})", normalized)
        if year_month:
            return date(int(year_month.group(1)), int(year_month.group(2)), 1)

        year_only = re.fullmatch(r"(\d{4})", normalized)
        if year_only:
            return date(int(year_only.group(1)), 1, 1)

        return None

    def _merge_periods(self, periods: Iterable[ExperiencePeriod]) -> list[ExperiencePeriod]:
        sorted_periods = sorted(periods, key=lambda period: (period.start, period.end))
        merged: list[ExperiencePeriod] = []

        for period in sorted_periods:
            if not merged:
                merged.append(period)
                continue

            last = merged[-1]
            if period.start <= self._add_months(last.end, 1):
                merged[-1] = ExperiencePeriod(start=last.start, end=max(last.end, period.end))
            else:
                merged.append(period)

        return merged

    def _calculate_total_years(self, periods: list[ExperiencePeriod]) -> float:
        total_days = sum((period.end - period.start).days for period in periods)
        return total_days / 365.25

    def _add_months(self, value: date, months: int) -> date:
        month_index = value.month - 1 + months
        year = value.year + month_index // 12
        month = month_index % 12 + 1
        day = min(value.day, 28)
        return date(year, month, day)

    def _is_section_heading(self, value: str) -> bool:
        normalized = self._clean_line(value).lower().strip(" :-")
        return normalized in SECTION_HEADINGS

    def _looks_like_new_section(self, value: str) -> bool:
        lowered = self._clean_line(value).lower().strip(" :-")
        return lowered in {
            "summary",
            "skills",
            "education",
            "projects",
            "certifications",
            "awards",
            "interests",
            "publications",
        }

    def _looks_like_experience_content(self, value: str) -> bool:
        return bool(self._contains_date_range(value) or self._looks_like_title(value) or self._looks_like_company(value))

    def _contains_date_range(self, value: str) -> bool:
        return bool(DATE_RANGE_PATTERN.search(value))

    def _looks_like_title(self, value: str) -> bool:
        lowered = value.lower()
        if any(stopword in lowered for stopword in TITLE_STOPWORDS):
            return False

        if self._contains_date_range(value):
            return False

        token_count = len([token for token in value.split() if token])
        if token_count == 0 or token_count > 12:
            return False

        return any(hint in lowered for hint in TITLE_HINTS) or lowered.endswith(("engineer", "developer", "analyst", "manager", "consultant", "architect", "designer", "scientist", "specialist", "lead", "director"))

    def _looks_like_company(self, value: str) -> bool:
        lowered = value.lower()
        if self._looks_like_title(value):
            return False
        company_markers = {"inc", "llc", "ltd", "corp", "corporation", "company", "co.", "gmbh", "plc", "solutions", "technologies", "labs", "studio", "group", "systems", "consulting", "global"}
        if any(marker in lowered for marker in company_markers):
            return True

        token_count = len([token for token in value.split() if token])
        if 1 <= token_count <= 5 and any(char.isalpha() for char in value):
            return value[:1].isupper() or any(char in value for char in ("&", "."))

        return False

    def _looks_like_composite_experience_line(self, value: str) -> bool:
        lowered = value.lower()
        return any(marker in lowered for marker in ("|", "@", " at "))

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

    def _calculate_confidence(
        self,
        chunk: list[str],
        title: str | None,
        company: str | None,
        date_range: ExperiencePeriod | None,
    ) -> float:
        score = 0.2
        if title:
            score += 0.25
        if company:
            score += 0.25
        if date_range:
            score += 0.3
        if any(self._contains_date_range(line) for line in chunk):
            score += 0.1
        return min(1.0, score)

