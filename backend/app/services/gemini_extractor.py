"""Gemini-powered structured resume extraction."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from google import genai
from google.genai import types

from backend.app.modules.prompt_builder import build_extraction_prompt


class GeminiExtractionError(RuntimeError):
    pass


class GeminiResumeExtractor:
    DEFAULT_MODEL = "gemini-2.0-flash"

    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL) -> None:
        resolved = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not resolved:
            raise EnvironmentError("GEMINI_API_KEY is required for Gemini resume extraction.")
        self.client = genai.Client(api_key=resolved)
        self.model = model

    def extract(self, resume_text: str) -> dict[str, Any]:
        system_prompt, user_prompt = build_extraction_prompt(resume_text)
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )
        except Exception as exc:
            raise GeminiExtractionError(f"Gemini extraction failed: {exc}") from exc

        raw = (getattr(response, "text", None) or "").strip()
        if not raw:
            raise GeminiExtractionError("Gemini returned empty extraction response.")
        data = self._parse_json(raw)
        return self._normalize(data)

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        raise GeminiExtractionError("Could not parse Gemini extraction JSON.")

    @staticmethod
    def _normalize(data: dict[str, Any]) -> dict[str, Any]:
        skills = data.get("skills") or []
        if isinstance(skills, dict):
            skills = [str(v) for v in skills.values()]
        skills = [str(s).strip() for s in skills if str(s).strip()]

        work = data.get("work_experience") or data.get("work_history") or []
        education = data.get("education") or []
        certs = data.get("certifications") or []
        projects = data.get("projects") or []

        return {
            "full_name": data.get("full_name"),
            "email": data.get("email"),
            "phone_number": data.get("phone"),
            "phone": data.get("phone"),
            "location": data.get("location"),
            "linkedin_url": data.get("linkedin_url"),
            "github_url": data.get("github_url"),
            "summary": data.get("summary"),
            "experience_years": data.get("years_experience"),
            "years_experience": data.get("years_experience"),
            "education": education,
            "skills": skills,
            "work_history": work,
            "work_experience": work,
            "certifications": certs,
            "projects": projects,
        }
