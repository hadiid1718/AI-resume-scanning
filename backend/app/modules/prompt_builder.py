"""Prompt construction for the Gemini-powered AI Candidate Evaluation Engine.

This module turns structured candidate / job dictionaries into a
(system_instruction, user_prompt) pair. The prompt instructs Gemini to analyse
the candidate across three dimensions — Skills, Experience, Education — and to
return a strict JSON object that the evaluation engine can parse deterministically.
"""

from __future__ import annotations

import json
from typing import Any


# ---------------------------------------------------------------------------
# Field normalisation helpers
# ---------------------------------------------------------------------------
# Candidate / job dictionaries arrive from several producers (the resume
# extraction pipeline, the JD parser, ad-hoc API payloads). These helpers read
# whichever key is present so the prompt builder is tolerant of every shape.


def _first(source: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        value = source.get(key)
        if value not in (None, "", [], {}):
            return value
    return default


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [str(item) for item in value.values()]
    if isinstance(value, (list, tuple, set)):
        flat: list[str] = []
        for item in value:
            if isinstance(item, dict):
                # e.g. skill match dicts {"name": "Python", ...}
                name = item.get("name") or item.get("skill") or item.get("title")
                flat.append(str(name) if name else json.dumps(item, ensure_ascii=False))
            else:
                flat.append(str(item))
        return [item for item in flat if item.strip()]
    return [str(value)]


def _list_block(items: list[str], bullet: str = "-") -> str:
    if not items:
        return "  (none provided)"
    return "\n".join(f"  {bullet} {item}" for item in items)


def _section(title: str, content: str) -> str:
    return f"### {title}\n{content}"


# ---------------------------------------------------------------------------
# Candidate / Job block builders
# ---------------------------------------------------------------------------


def build_candidate_block(candidate: dict[str, Any]) -> str:
    """Serialise a candidate dictionary into a readable prompt block."""
    name = _first(candidate, "name", "full_name", default="Unknown Candidate")
    email = _first(candidate, "email", default="N/A")
    years_exp = _first(
        candidate, "years_experience", "experience_years", "total_experience_years", default="N/A"
    )

    education_block = _list_block(_as_list(_first(candidate, "education", "educations", default=[])))
    skills_block = _list_block(_as_list(_first(candidate, "skills", "categorized_skills", default=[])))
    certs_block = _list_block(_as_list(_first(candidate, "certifications", "certificates", default=[])))

    work_history = _first(candidate, "work_history", "experience", "experiences", default=[])
    if isinstance(work_history, list) and work_history and isinstance(work_history[0], dict):
        wh_lines: list[str] = []
        for job in work_history:
            title = job.get("title") or job.get("position") or "N/A"
            company = job.get("company") or job.get("employer") or "N/A"
            duration = job.get("duration") or job.get("dates") or "N/A"
            summary = job.get("summary") or job.get("description") or ""
            wh_lines.append(f"  - {title} @ {company} ({duration})")
            if summary:
                wh_lines.append(f"    {summary}")
        work_block = "\n".join(wh_lines)
    else:
        work_block = _list_block(_as_list(work_history))

    return (
        "CANDIDATE PROFILE\n"
        f"  Name            : {name}\n"
        f"  Email           : {email}\n"
        f"  Years of Exp.   : {years_exp}\n\n"
        f"{_section('Education', education_block)}\n\n"
        f"{_section('Skills', skills_block)}\n\n"
        f"{_section('Certifications', certs_block)}\n\n"
        f"{_section('Work History', work_block)}"
    )


def build_job_block(job: dict[str, Any]) -> str:
    """Serialise a job-requirement dictionary into a readable prompt block."""
    title = _first(job, "title", "role", default="Unknown Role")
    company = _first(job, "company", default="Unknown Company")
    req_exp = _first(job, "required_experience_years", "experience_required", default="N/A")
    req_edu = _first(job, "required_education", "education_requirements", default="N/A")
    if isinstance(req_edu, list):
        req_edu = ", ".join(str(item) for item in req_edu) or "N/A"
    description = _first(job, "description", default="")

    req_skills = _list_block(_as_list(_first(job, "required_skills", "skills", default=[])))
    pref_skills = _list_block(_as_list(_first(job, "preferred_skills", "nice_to_have", default=[])))

    desc_section = f"{_section('Job Description', f'  {description}')}\n\n" if description else ""

    return (
        "JOB REQUIREMENTS\n"
        f"  Role            : {title}\n"
        f"  Company         : {company}\n"
        f"  Required Exp.   : {req_exp} year(s)\n"
        f"  Required Edu.   : {req_edu}\n\n"
        f"{desc_section}"
        f"{_section('Required Skills', req_skills)}\n\n"
        f"{_section('Preferred Skills', pref_skills)}"
    )


# ---------------------------------------------------------------------------
# System instruction + JSON contract
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a senior technical recruiter and talent-evaluation specialist with 15+ years of \
experience assessing software engineering, AI/ML, and technology candidates.

Evaluate the candidate strictly against the job requirements across three dimensions:
  1. SKILLS      - coverage of required/preferred skills, depth, and transferable skills.
  2. EXPERIENCE  - years, relevance, seniority, and impact of past roles.
  3. EDUCATION   - degree relevance, level, and academic signals.

Scoring rubric (return a single integer 0-100):
  85-100  Excellent  - exceeds requirements, strong hire.
  70-84   Strong     - meets requirements with minor gaps.
  55-69   Moderate   - partial fit, notable gaps.
  40-54   Weak       - significant gaps.
  0-39    Poor       - not a fit.

Weighting guidance: Skills ~45%, Experience ~35%, Education ~20% (adjust sensibly to the role).

Be objective, concise, and recruiter-friendly. Justify the score with concrete evidence
from the profile. Never invent facts that are not present in the candidate data.

Respond with a SINGLE valid JSON object and NOTHING else (no markdown, no code fences).
"""

# The exact JSON contract the model must follow.
JSON_SCHEMA_HINT = """\
{
  "score": <integer 0-100>,
  "verdict": "<Strongly Recommend | Recommend | Conditional Recommend | Do Not Recommend>",
  "summary": "<2-3 sentence recruiter-friendly summary of the candidate for THIS role>",
  "skills_analysis": "<2-4 sentences: matched skills, missing skills, depth>",
  "experience_analysis": "<2-4 sentences: years, relevance, seniority, impact>",
  "education_analysis": "<1-3 sentences: degree relevance and level>",
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "weaknesses": ["<gap 1>", "<gap 2>"],
  "recommendations": ["<actionable recommendation 1>", "<actionable recommendation 2>"]
}
"""


# ---------------------------------------------------------------------------
# Main prompt builder
# ---------------------------------------------------------------------------


def build_evaluation_prompt(
    candidate: dict[str, Any],
    job: dict[str, Any],
    match_result: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Build a ``(system_instruction, user_prompt)`` tuple for Gemini.

    Parameters
    ----------
    candidate    : Candidate profile dictionary.
    job          : Job requirement dictionary.
    match_result : Optional pre-computed match signals (overlap_skills,
                   missing_skills, score) to ground the model.
    """
    candidate_block = build_candidate_block(candidate)
    job_block = build_job_block(job)

    if match_result:
        overlap = _list_block(_as_list(match_result.get("overlap_skills", [])))
        missing = _list_block(_as_list(match_result.get("missing_skills", [])))
        pre_score = match_result.get("score")
        pre_score_line = f"  Pre-computed match score : {pre_score}/100\n" if pre_score is not None else ""
        match_block = (
            "\nPRE-COMPUTED MATCH SIGNALS (reference only — form your own judgement)\n"
            f"{pre_score_line}"
            f"{_section('Overlapping Skills', overlap)}\n\n"
            f"{_section('Missing Skills', missing)}\n"
        )
    else:
        match_block = ""

    separator = "=" * 68
    user_prompt = (
        "Analyse the candidate below against the job requirements and return the evaluation.\n\n"
        f"{separator}\n{candidate_block}\n{separator}\n{job_block}\n{match_block}{separator}\n\n"
        "Return ONLY a JSON object matching this exact schema (same keys, same types):\n\n"
        f"{JSON_SCHEMA_HINT}"
    )

    return SYSTEM_PROMPT, user_prompt


EXTRACTION_SYSTEM_PROMPT = """\
You are an expert resume parser. Extract structured information from resume text.
Return ONLY valid JSON matching the schema. Do not invent information not present in the resume.
If a field is missing, use null for strings, empty arrays for lists.
"""

EXTRACTION_JSON_SCHEMA = """\
{
  "full_name": "<string or null>",
  "email": "<string or null>",
  "phone": "<string or null>",
  "location": "<string or null>",
  "linkedin_url": "<string or null>",
  "github_url": "<string or null>",
  "summary": "<string or null>",
  "years_experience": <number or null>,
  "education": [{"degree": "", "institution": "", "year": "", "details": ""}],
  "skills": ["<skill>"],
  "work_experience": [{"title": "", "company": "", "duration": "", "summary": ""}],
  "certifications": ["<certification>"],
  "projects": [{"name": "", "description": "", "technologies": []}]
}
"""


def build_extraction_prompt(resume_text: str) -> tuple[str, str]:
    user_prompt = (
        "Extract structured resume information from the text below.\n\n"
        f"RESUME TEXT:\n{resume_text[:12000]}\n\n"
        "Return ONLY a JSON object matching this schema:\n"
        f"{EXTRACTION_JSON_SCHEMA}"
    )
    return EXTRACTION_SYSTEM_PROMPT, user_prompt


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sample_candidate = {
        "name": "Hadeed Hassan",
        "email": "hadeed@example.com",
        "years_experience": 3,
        "education": ["BS Information Technology - Quaid-i-Azam University (2024)"],
        "skills": ["Python", "React", "Node.js", "MongoDB", "AWS", "REST APIs", "SQL"],
        "certifications": ["AWS Certified Cloud Practitioner"],
        "work_history": [
            {
                "title": "Software Engineering Intern",
                "company": "TechCorp",
                "duration": "6 months",
                "summary": "Built REST APIs with Node.js and deployed services on AWS Lambda.",
            }
        ],
    }
    sample_job = {
        "title": "AI Software Engineer",
        "company": "SoftPyramid",
        "required_experience_years": 2,
        "required_education": "BS Computer Science or related field",
        "required_skills": ["Python", "Machine Learning", "AWS", "REST APIs"],
        "preferred_skills": ["Kubernetes", "Docker", "PyTorch"],
        "description": "Build and deploy AI-powered backend services at scale.",
    }
    sample_match = {
        "score": 74,
        "overlap_skills": ["Python", "AWS", "REST APIs"],
        "missing_skills": ["Machine Learning", "Kubernetes", "Docker"],
    }

    system_prompt, user_prompt = build_evaluation_prompt(sample_candidate, sample_job, sample_match)
    print("=== SYSTEM INSTRUCTION ===")
    print(system_prompt)
    print("\n=== USER PROMPT ===")
    print(user_prompt)
