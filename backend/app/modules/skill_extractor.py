from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

import spacy


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SkillMatch:
    category: str
    normalized_name: str
    confidence: float
    source: str


class SkillExtractor:
    def __init__(self, dictionary_path: str | Path | None = None) -> None:
        self.dictionary_path = Path(dictionary_path) if dictionary_path else Path(__file__).with_name("skills_dictionary.json")
        self.skills_dictionary = self._load_dictionary()
        self.nlp = spacy.blank("en")
        if "sentencizer" not in self.nlp.pipe_names:
            self.nlp.add_pipe("sentencizer")

    def extract(self, text: str) -> dict:
        normalized_text = self._normalize_text(text)
        doc = self.nlp(normalized_text)
        lower_text = normalized_text.lower()

        matches: dict[str, dict[str, SkillMatch]] = {
            category: {} for category in self.skills_dictionary
        }

        for category, skills in self.skills_dictionary.items():
            for canonical_name, aliases in skills.items():
                confidence = self._score_skill(canonical_name, aliases, lower_text, doc)
                if confidence <= 0:
                    continue

                match = SkillMatch(
                    category=category,
                    normalized_name=canonical_name,
                    confidence=confidence,
                    source=self._match_source(canonical_name, aliases, lower_text),
                )
                matches[category][canonical_name] = match

        categorized_skills = {
            category: [
                {
                    "name": match.normalized_name,
                    "confidence": round(match.confidence, 2),
                    "source": match.source,
                }
                for match in sorted(category_matches.values(), key=lambda item: (-item.confidence, item.normalized_name))
            ]
            for category, category_matches in matches.items()
        }

        flattened_skills = [
            {
                "name": match.normalized_name,
                "category": match.category,
                "confidence": round(match.confidence, 2),
                "source": match.source,
            }
            for category_matches in matches.values()
            for match in category_matches.values()
        ]
        flattened_skills.sort(key=lambda item: item["name"])

        confidence_scores = {
            category: round(
                sum(skill["confidence"] for skill in skills) / len(skills),
                2,
            )
            if skills
            else 0.0
            for category, skills in categorized_skills.items()
        }

        return {
            "skills": [item["name"] for item in flattened_skills],
            "categorized_skills": categorized_skills,
            "confidence_scores": confidence_scores,
            "all_matches": flattened_skills,
        }

    def _load_dictionary(self) -> dict[str, dict[str, list[str]]]:
        try:
            raw_dictionary = json.loads(self.dictionary_path.read_text(encoding="utf-8"))
            return {
                category: {
                    self._normalize_skill_name(canonical_name): [self._normalize_alias(alias) for alias in aliases]
                    for canonical_name, aliases in category_entries.items()
                }
                for category, category_entries in raw_dictionary.items()
            }
        except Exception:
            logger.exception("Unable to load skills dictionary from %s", self.dictionary_path)
            raise

    def _score_skill(self, canonical_name: str, aliases: list[str], lower_text: str, doc: spacy.tokens.Doc) -> float:
        alias_hits = 0
        alias_weight = 0.0

        normalized_canonical = self._normalize_alias(canonical_name)
        if self._match_text(normalized_canonical, lower_text):
            alias_hits += 1
            alias_weight += 0.9

        for alias in aliases:
            if self._match_text(alias, lower_text):
                alias_hits += 1
                alias_weight += 1.0 if " " not in alias else 0.95

        nlp_bonus = self._nlp_bonus(canonical_name, aliases, doc)
        if alias_hits == 0 and nlp_bonus == 0:
            return 0.0

        raw_score = min(1.0, 0.2 + alias_weight / max(1, len(aliases) + 1) + nlp_bonus)
        return round(raw_score, 4)

    def _nlp_bonus(self, canonical_name: str, aliases: list[str], doc: spacy.tokens.Doc) -> float:
        text = doc.text.lower()
        tokens = [token.text.lower() for token in doc if not token.is_space]
        canonical_tokens = self._normalize_alias(canonical_name).split()
        if canonical_tokens and all(token in tokens for token in canonical_tokens):
            return 0.1
        for alias in aliases:
            alias_tokens = alias.split()
            if alias_tokens and all(token in tokens for token in alias_tokens):
                return 0.08
            if alias in text:
                return 0.05
        return 0.0

    def _match_source(self, canonical_name: str, aliases: list[str], lower_text: str) -> str:
        for alias in [self._normalize_alias(canonical_name), *aliases]:
            if self._match_text(alias, lower_text):
                return alias
        return canonical_name

    def _match_text(self, needle: str, haystack: str) -> bool:
        pattern = r"(?<!\w)" + re.escape(needle) + r"(?!\w)"
        return bool(re.search(pattern, haystack))

    def _normalize_text(self, text: str) -> str:
        return "\n".join(" ".join(line.split()) for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n") if line.strip())

    def _normalize_skill_name(self, value: str) -> str:
        return " ".join(value.split()).strip()

    def _normalize_alias(self, value: str) -> str:
        return self._normalize_skill_name(value).lower()
