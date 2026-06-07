from __future__ import annotations
 
import json
import os
import re
import textwrap
from typing import Any
 
from openai import OpenAI
 
from backend.app.modules.prompt_builder import build_evaluation_prompt
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Engine
# ─────────────────────────────────────────────────────────────────────────────
 
class AIEvaluationEngine:
    """
    Senior-grade AI evaluation engine for candidate assessment.
 
    Parameters
    ----------
    api_key : str, optional
        OpenAI API key. Falls back to the ``OPENAI_API_KEY`` env-var.
    model : str
        OpenAI chat model to use. Defaults to ``gpt-4o``.
    temperature : float
        Sampling temperature (0 = deterministic, 1 = creative).
    """
 
    DEFAULT_MODEL = "gpt-4o"
 
    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.3,
    ) -> None:
        resolved_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not resolved_key:
            raise EnvironmentError(
                "OpenAI API key not found. Pass api_key= or set OPENAI_API_KEY."
            )
        self.client      = OpenAI(api_key=resolved_key)
        self.model       = model
        self.temperature = temperature
 
    # ------------------------------------------------------------------ #
    # Public interface                                                     #
    # ------------------------------------------------------------------ #
 
    def evaluate(
        self,
        candidate: dict[str, Any],
        job: dict[str, Any],
        match_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Run a full AI evaluation.
 
        Parameters
        ----------
        candidate    : Candidate profile dict (see prompt_builder for schema).
        job          : Job requirements dict.
        match_result : Optional pre-computed match signals to enrich the prompt.
 
        Returns
        -------
        Structured evaluation dict with keys:
            raw_report, score, verdict, summary, strengths,
            weaknesses, recommendations, overall_assessment
        """
        system_prompt, user_prompt = build_evaluation_prompt(
            candidate, job, match_result
        )
 
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
        )
 
        raw_report = response.choices[0].message.content.strip()
        return self._parse_report(raw_report, candidate, job)
 
    # ------------------------------------------------------------------ #
    # Report parsing                                                       #
    # ------------------------------------------------------------------ #
 
    @staticmethod
    def _extract_section(raw: str, heading: str) -> str:
        """
        Pull the text body that follows a markdown ``### Heading`` up to
        the next ``---`` or ``###`` separator.
        """
        pattern = rf"###\s+{re.escape(heading)}\s*\n(.*?)(?=\n---|\n###|\Z)"
        match = re.search(pattern, raw, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""
 
    @staticmethod
    def _extract_bullets(section_text: str) -> list[str]:
        """Parse markdown bullet lines (``-`` or ``*`` or ``1.``) into a list."""
        lines = []
        for line in section_text.splitlines():
            line = line.strip()
            cleaned = re.sub(r"^[-*•]\s+|^\d+\.\s+", "", line)
            if cleaned:
                lines.append(cleaned)
        return lines
 
    @staticmethod
    def _extract_score(raw: str) -> int:
        """Extract the first integer in a ``Score: N/100`` pattern."""
        match = re.search(r"\*{0,2}Score[:\s]+(\d{1,3})\s*/\s*100", raw, re.IGNORECASE)
        if match:
            return min(100, max(0, int(match.group(1))))
        # Fallback: first bare integer that looks like a score
        match = re.search(r"\b([0-9]{1,3})\s*/\s*100\b", raw)
        return min(100, max(0, int(match.group(1)))) if match else 0
 
    @staticmethod
    def _extract_verdict(raw: str) -> str:
        """Pull the hiring verdict line."""
        match = re.search(
            r"\*{0,2}Verdict[:\s*]*\*{0,2}\s*(.+)",
            raw,
            re.IGNORECASE,
        )
        if match:
            verdict = match.group(1).strip().strip("*").strip()
            return verdict
        return "Unspecified"
 
    def _parse_report(
        self,
        raw: str,
        candidate: dict,
        job: dict,
    ) -> dict[str, Any]:
        score   = self._extract_score(raw)
        verdict = self._extract_verdict(raw)
 
        summary_text    = self._extract_section(raw, "Candidate Summary")
        strengths_text  = self._extract_section(raw, "Strengths")
        weaknesses_text = self._extract_section(raw, r"Weaknesses\s*/?\s*Gaps?")
        recs_text       = self._extract_section(raw, "Recommendations for the Recruiter")
 
        strengths       = self._extract_bullets(strengths_text)
        weaknesses      = self._extract_bullets(weaknesses_text)
        recommendations = self._extract_bullets(recs_text)
 
        overall = (
            "highly_recommended"   if score >= 80 else
            "recommended"          if score >= 65 else
            "conditional"          if score >= 50 else
            "needs_improvement"
        )
 
        return {
            "raw_report":          raw,
            "score":               score,
            "verdict":             verdict,
            "overall_assessment":  overall,
            "candidate_name":      candidate.get("name", "N/A"),
            "role":                job.get("title", "N/A"),
            "company":             job.get("company", "N/A"),
            "summary":             summary_text,
            "strengths":           strengths,
            "weaknesses":          weaknesses,
            "recommendations":     recommendations,
        }
 
    # ------------------------------------------------------------------ #
    # Recruiter-friendly display                                           #
    # ------------------------------------------------------------------ #
 
    @staticmethod
    def _score_bar(score: int, width: int = 30) -> str:
        """Render a simple ASCII progress bar."""
        filled = round(score / 100 * width)
        bar    = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {score}/100"
 
    @staticmethod
    def _verdict_colour(verdict: str) -> str:
        """Map verdict → emoji indicator."""
        v = verdict.lower()
        if "strongly" in v:
            return "🟢"
        if "do not" in v or "not recommend" in v:
            return "🔴"
        if "conditional" in v:
            return "🟡"
        return "🟢"
 
    def print_report(self, result: dict[str, Any]) -> None:
        """Pretty-print the evaluation result to stdout."""
        W = 64
        sep = "─" * W
 
        def bullets(items: list[str], prefix: str = "  •") -> str:
            if not items:
                return "  (none identified)"
            return "\n".join(f"{prefix} {i}" for i in items)
 
        verdict_icon = self._verdict_colour(result["verdict"])
        score_bar    = self._score_bar(result["score"])
 
        print(f"\n{'═'*W}")
        print(f"  🤖  AI CANDIDATE EVALUATION REPORT")
        print(f"{'═'*W}")
        print(f"  Candidate : {result['candidate_name']}")
        print(f"  Role      : {result['role']} @ {result['company']}")
        print(sep)
 
        print(f"\n  OVERALL SCORE")
        print(f"  {score_bar}")
        print(f"  Assessment : {result['overall_assessment'].replace('_', ' ').title()}")
 
        print(f"\n{sep}")
        print(f"  CANDIDATE SUMMARY")
        wrapped = textwrap.fill(result["summary"], width=W - 4, initial_indent="  ", subsequent_indent="  ")
        print(wrapped)
 
        print(f"\n{sep}")
        print(f"  ✅  STRENGTHS")
        print(bullets(result["strengths"]))
 
        print(f"\n{sep}")
        print(f"  ⚠️   WEAKNESSES / GAPS")
        print(bullets(result["weaknesses"]))
 
        print(f"\n{sep}")
        print(f"  💡  RECOMMENDATIONS")
        for i, rec in enumerate(result["recommendations"], 1):
            print(textwrap.fill(
                f"  {i}. {rec}",
                width=W - 2,
                subsequent_indent="     ",
            ))
 
        print(f"\n{sep}")
        print(f"  HIRING RECOMMENDATION")
        print(f"  {verdict_icon}  {result['verdict']}")
        print(f"{'═'*W}\n")
 
    def to_json(self, result: dict[str, Any], indent: int = 2) -> str:
        """Serialise result to JSON (excludes the raw_report for brevity)."""
        exportable = {k: v for k, v in result.items() if k != "raw_report"}
        return json.dumps(exportable, indent=indent, ensure_ascii=False)
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Demo / CLI runner
# ─────────────────────────────────────────────────────────────────────────────
 
def _demo() -> None:
    """Run a demonstration evaluation with a sample candidate and job."""
 
    candidate = {
        "name": "Hadeed Hassan",
        "email": "hadeed@example.com",
        "years_experience": 3,
        "education": [
            "BS Information Technology — Quaid-i-Azam University (2024)"
        ],
        "skills": [
            "Python", "React", "Node.js", "MongoDB",
            "AWS", "REST APIs", "SQL", "Git",
        ],
        "certifications": ["AWS Certified Cloud Practitioner"],
        "work_history": [
            {
                "title": "Software Engineering Intern",
                "company": "TechCorp",
                "duration": "6 months",
                "summary": (
                    "Built and deployed REST APIs with Node.js on AWS Lambda; "
                    "integrated MongoDB for data persistence."
                ),
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
        "description": (
            "Design and deploy AI-powered backend services at scale. "
            "Work closely with ML researchers to productionise models."
        ),
    }
 
    match_result = {
        "score": 74,
        "overlap_skills": ["Python", "AWS", "REST APIs"],
        "missing_skills": ["Machine Learning", "Kubernetes", "Docker", "PyTorch"],
    }
 
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print(
            "⚠  OPENAI_API_KEY not set — cannot run live evaluation.\n"
            "   Set the env-var and re-run: export OPENAI_API_KEY=sk-...\n"
        )
        # Show what the prompt looks like without calling the API
        from backend.app.modules.prompt_builder import build_evaluation_prompt
        sys_p, user_p = build_evaluation_prompt(candidate, job, match_result)
        print("=== SYSTEM PROMPT (preview) ===")
        print(sys_p[:400], "...\n")
        print("=== USER PROMPT (preview) ===")
        print(user_p[:800], "...")
        return
 
    engine = AIEvaluationEngine(api_key=api_key)
 
    print("🔍  Evaluating candidate — calling OpenAI API …")
    result = engine.evaluate(candidate, job, match_result)
 
    # Recruiter-friendly terminal output
    engine.print_report(result)
 
    # Also dump structured JSON
    print("📄  Structured JSON output:")
    print(engine.to_json(result))
 
 
if __name__ == "__main__":
    _demo()