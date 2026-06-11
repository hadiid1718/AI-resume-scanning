"""Module 9 - AI Scoring Engine.

A Gemini-powered candidate evaluation engine. It analyses a candidate against a
job across Skills, Experience, and Education, then produces a recruiter-friendly
report with a 0-100 score, summary, strengths, weaknesses, and recommendations.

The public surface (``AIEvaluationEngine.evaluate``) returns a dict that is
drop-in compatible with ``backend.app.schemas.ai_evaluation.AIEvaluationResponse``.
"""

from __future__ import annotations

import json
import os
import re
import textwrap
from typing import Any

from google import genai
from google.genai import types

from backend.app.modules.prompt_builder import build_evaluation_prompt


class AIEvaluationError(RuntimeError):
    """Raised when the Gemini call or its response cannot be processed."""


class AIEvaluationEngine:
    """Senior-grade AI evaluation engine backed by the Google Gemini API.

    Parameters
    ----------
    api_key : str, optional
        Gemini API key. Falls back to ``GEMINI_API_KEY`` / ``GOOGLE_API_KEY``.
    model : str
        Gemini model id. Defaults to ``gemini-2.0-flash``.
    temperature : float
        Sampling temperature (0 = deterministic, 1 = creative).
    """

    DEFAULT_MODEL = "gemini-2.0-flash"

    # Keys we expect back from the model (see prompt_builder.JSON_SCHEMA_HINT).
    _REQUIRED_KEYS = (
        "score",
        "verdict",
        "summary",
        "skills_analysis",
        "experience_analysis",
        "education_analysis",
        "strengths",
        "weaknesses",
        "recommendations",
    )

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.3,
    ) -> None:
        resolved_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not resolved_key:
            raise EnvironmentError(
                "Gemini API key not found. Pass api_key= or set GEMINI_API_KEY (or GOOGLE_API_KEY)."
            )
        self.client = genai.Client(api_key=resolved_key)
        self.model = model
        self.temperature = temperature

    # ------------------------------------------------------------------ #
    # Public interface                                                    #
    # ------------------------------------------------------------------ #

    def evaluate(
        self,
        candidate: dict[str, Any],
        job: dict[str, Any],
        match_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run a full AI evaluation and return a structured report dict."""
        system_prompt, user_prompt = build_evaluation_prompt(candidate, job, match_result)

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=self.temperature,
                    response_mime_type="application/json",
                ),
            )
        except Exception as exc:  # network / auth / quota errors
            raise AIEvaluationError(f"Gemini request failed: {exc}") from exc

        raw_text = (getattr(response, "text", None) or "").strip()
        if not raw_text:
            raise AIEvaluationError("Gemini returned an empty response.")

        data = self._parse_json(raw_text)
        return self._build_result(data, raw_text, candidate, job)

    def evaluate_batch(
        self,
        items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Evaluate several candidates and return results ranked by score (desc).

        Each item is a dict with ``candidate``, ``job`` and optional ``match_result``.
        """
        results = [
            self.evaluate(
                candidate=item.get("candidate", {}),
                job=item.get("job", {}),
                match_result=item.get("match_result"),
            )
            for item in items
        ]
        return sorted(results, key=lambda r: r["score"], reverse=True)

    # ------------------------------------------------------------------ #
    # Response parsing                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        """Parse JSON, tolerating code fences or surrounding prose."""
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # Strip ```json ... ``` fences if present.
        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if fenced:
            try:
                return json.loads(fenced.group(1))
            except json.JSONDecodeError:
                pass

        # Fall back to the first balanced-looking {...} block.
        brace = re.search(r"\{.*\}", raw, re.DOTALL)
        if brace:
            try:
                return json.loads(brace.group(0))
            except json.JSONDecodeError as exc:
                raise AIEvaluationError(f"Could not parse Gemini JSON response: {exc}") from exc

        raise AIEvaluationError("Gemini response did not contain a JSON object.")

    def _build_result(
        self,
        data: dict[str, Any],
        raw: str,
        candidate: dict[str, Any],
        job: dict[str, Any],
    ) -> dict[str, Any]:
        score = self._clamp_score(data.get("score", 0))
        verdict = str(data.get("verdict") or "Unspecified").strip()

        overall = (
            "highly_recommended" if score >= 80
            else "recommended" if score >= 65
            else "conditional" if score >= 50
            else "needs_improvement"
        )

        return {
            "raw_report": raw,
            "score": score,
            "verdict": verdict,
            "overall_assessment": overall,
            "candidate_name": candidate.get("name") or candidate.get("full_name") or "N/A",
            "role": job.get("title") or job.get("role") or "N/A",
            "company": job.get("company") or "N/A",
            "summary": str(data.get("summary") or "").strip(),
            "skills_analysis": str(data.get("skills_analysis") or "").strip(),
            "experience_analysis": str(data.get("experience_analysis") or "").strip(),
            "education_analysis": str(data.get("education_analysis") or "").strip(),
            "strengths": self._as_str_list(data.get("strengths")),
            "weaknesses": self._as_str_list(data.get("weaknesses")),
            "recommendations": self._as_str_list(data.get("recommendations")),
        }

    @staticmethod
    def _clamp_score(value: Any) -> int:
        try:
            number = int(round(float(value)))
        except (TypeError, ValueError):
            match = re.search(r"\d{1,3}", str(value))
            number = int(match.group(0)) if match else 0
        return max(0, min(100, number))

    @staticmethod
    def _as_str_list(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value.strip()] if value.strip() else []
        if isinstance(value, (list, tuple)):
            return [str(item).strip() for item in value if str(item).strip()]
        return [str(value).strip()]

    # ------------------------------------------------------------------ #
    # Recruiter-friendly display                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _score_bar(score: int, width: int = 30) -> str:
        filled = round(score / 100 * width)
        bar = "#" * filled + "-" * (width - filled)
        return f"[{bar}] {score}/100"

    @staticmethod
    def _verdict_icon(verdict: str) -> str:
        v = verdict.lower()
        if "strongly" in v:
            return "[++]"
        if "do not" in v or "not recommend" in v:
            return "[--]"
        if "conditional" in v:
            return "[~]"
        return "[+]"

    def render_report(self, result: dict[str, Any]) -> str:
        """Return a recruiter-friendly plain-text report (also used by print_report)."""
        width = 66
        sep = "-" * width

        def bullets(items: list[str], prefix: str = "  - ") -> str:
            return "\n".join(f"{prefix}{item}" for item in items) if items else "  (none identified)"

        def para(text: str) -> str:
            if not text:
                return "  (not provided)"
            return textwrap.fill(text, width=width - 2, initial_indent="  ", subsequent_indent="  ")

        lines = [
            "=" * width,
            "  AI CANDIDATE EVALUATION REPORT",
            "=" * width,
            f"  Candidate : {result['candidate_name']}",
            f"  Role      : {result['role']} @ {result['company']}",
            sep,
            "  OVERALL SCORE",
            f"  {self._score_bar(result['score'])}",
            f"  Assessment : {result['overall_assessment'].replace('_', ' ').title()}",
            sep,
            "  CANDIDATE SUMMARY",
            para(result["summary"]),
            sep,
            "  SKILLS ANALYSIS",
            para(result["skills_analysis"]),
            "  EXPERIENCE ANALYSIS",
            para(result["experience_analysis"]),
            "  EDUCATION ANALYSIS",
            para(result["education_analysis"]),
            sep,
            "  STRENGTHS",
            bullets(result["strengths"]),
            sep,
            "  WEAKNESSES / GAPS",
            bullets(result["weaknesses"]),
            sep,
            "  RECOMMENDATIONS",
            bullets([f"{i}. {rec}" for i, rec in enumerate(result["recommendations"], 1)], prefix="  "),
            sep,
            "  HIRING RECOMMENDATION",
            f"  {self._verdict_icon(result['verdict'])} {result['verdict']}",
            "=" * width,
        ]
        return "\n".join(lines)

    def print_report(self, result: dict[str, Any]) -> None:
        print(self.render_report(result))

    @staticmethod
    def to_json(result: dict[str, Any], indent: int = 2) -> str:
        """Serialise a result to JSON (excludes the verbose raw_report)."""
        exportable = {k: v for k, v in result.items() if k != "raw_report"}
        return json.dumps(exportable, indent=indent, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Demo / CLI runner
# ---------------------------------------------------------------------------

def _demo() -> None:
    candidate = {
        "name": "Hadeed Hassan",
        "email": "hadeed@example.com",
        "years_experience": 3,
        "education": ["BS Information Technology - Quaid-i-Azam University (2024)"],
        "skills": ["Python", "React", "Node.js", "MongoDB", "AWS", "REST APIs", "SQL", "Git"],
        "certifications": ["AWS Certified Cloud Practitioner"],
        "work_history": [
            {
                "title": "Software Engineering Intern",
                "company": "TechCorp",
                "duration": "6 months",
                "summary": "Built and deployed REST APIs with Node.js on AWS Lambda; used MongoDB.",
            }
        ],
    }
    job = {
        "title": "AI Software Engineer",
        "company": "SoftPyramid",
        "required_experience_years": 2,
        "required_education": "BS Computer Science or related field",
        "required_skills": ["Python", "Machine Learning", "AWS", "REST APIs"],
        "preferred_skills": ["Kubernetes", "Docker", "PyTorch", "FastAPI"],
        "description": "Design and deploy AI-powered backend services at scale.",
    }
    match_result = {
        "score": 74,
        "overlap_skills": ["Python", "AWS", "REST APIs"],
        "missing_skills": ["Machine Learning", "Kubernetes", "Docker", "PyTorch"],
    }

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print(
            "GEMINI_API_KEY not set - cannot run a live evaluation.\n"
            "  Set it and re-run:  setx GEMINI_API_KEY <your-key>  (or export on *nix)\n"
        )
        from backend.app.modules.prompt_builder import build_evaluation_prompt

        system_prompt, user_prompt = build_evaluation_prompt(candidate, job, match_result)
        print("=== SYSTEM INSTRUCTION (preview) ===")
        print(system_prompt[:400], "...\n")
        print("=== USER PROMPT (preview) ===")
        print(user_prompt[:800], "...")
        return

    engine = AIEvaluationEngine(api_key=api_key)
    print("Evaluating candidate - calling Gemini API ...")
    result = engine.evaluate(candidate, job, match_result)
    engine.print_report(result)
    print("\nStructured JSON output:")
    print(engine.to_json(result))


if __name__ == "__main__":
    _demo()
