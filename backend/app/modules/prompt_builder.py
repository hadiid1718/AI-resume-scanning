from __future__ import annotations
from typing import Any
 
 
# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------
 
def _list_block(items: list[str], bullet: str = "•") -> str:
    """Render a Python list as a bulleted text block."""
    if not items:
        return "  (none provided)"
    return "\n".join(f"  {bullet} {item}" for item in items)
 
 
def _section(title: str, content: str) -> str:
    """Wrap content in a labelled section."""
    return f"### {title}\n{content}"
 
 
# ---------------------------------------------------------------------------
# Candidate / Job block builders
# ---------------------------------------------------------------------------
 
def build_candidate_block(candidate: dict[str, Any]) -> str:
    """
    Serialise a candidate dictionary into a readable prompt block.
 
    Expected keys (all optional, gracefully handled if missing):
        name, email, years_experience, education, skills, certifications,
        work_history (list[dict] with keys: title, company, duration, summary)
    """
    name = candidate.get("name", "Unknown Candidate")
    email = candidate.get("email", "N/A")
    years_exp = candidate.get("years_experience", "N/A")
 
    # Education
    edu = candidate.get("education", [])
    if isinstance(edu, str):
        edu = [edu]
    education_block = _list_block(edu)
 
    # Skills
    skills = candidate.get("skills", [])
    skills_block = _list_block(skills)
 
    # Certifications
    certs = candidate.get("certifications", [])
    certs_block = _list_block(certs)
 
    # Work history
    work_history = candidate.get("work_history", [])
    if work_history:
        wh_lines = []
        for job in work_history:
            title   = job.get("title", "N/A")
            company = job.get("company", "N/A")
            duration = job.get("duration", "N/A")
            summary  = job.get("summary", "")
            wh_lines.append(f"  • {title} @ {company} ({duration})")
            if summary:
                wh_lines.append(f"    {summary}")
        work_block = "\n".join(wh_lines)
    else:
        work_block = "  (none provided)"
 
    return (
        f"CANDIDATE PROFILE\n"
        f"  Name            : {name}\n"
        f"  Email           : {email}\n"
        f"  Years of Exp.   : {years_exp}\n\n"
        f"{_section('Education', education_block)}\n\n"
        f"{_section('Skills', skills_block)}\n\n"
        f"{_section('Certifications', certs_block)}\n\n"
        f"{_section('Work History', work_block)}"
    )
 
 
def build_job_block(job: dict[str, Any]) -> str:
    """
    Serialise a job-requirement dictionary into a readable prompt block.
 
    Expected keys (all optional):
        title, company, required_skills, preferred_skills,
        required_experience_years, required_education, description
    """
    title   = job.get("title", "Unknown Role")
    company = job.get("company", "Unknown Company")
    req_exp = job.get("required_experience_years", "N/A")
    req_edu = job.get("required_education", "N/A")
    description = job.get("description", "")
 
    req_skills  = _list_block(job.get("required_skills", []))
    pref_skills = _list_block(job.get("preferred_skills", []))
 
    desc_section = (
        f"{_section('Job Description', f'  {description}')}\n\n"
        if description else ""
    )
 
    return (
        f"JOB REQUIREMENTS\n"
        f"  Role            : {title}\n"
        f"  Company         : {company}\n"
        f"  Required Exp.   : {req_exp} year(s)\n"
        f"  Required Edu.   : {req_edu}\n\n"
        f"{desc_section}"
        f"{_section('Required Skills', req_skills)}\n\n"
        f"{_section('Preferred Skills', pref_skills)}"
    )
 
 
# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
 
SYSTEM_PROMPT = """\
You are a senior technical recruiter and talent evaluation specialist with 15+ years
of experience assessing software engineering, AI/ML, and technology candidates.
 
Your job is to produce a structured, objective, recruiter-friendly evaluation report.
You must follow the EXACT output format specified in the user prompt — nothing more,
nothing less. Be concise, professional, and actionable.
"""
 
 
# ---------------------------------------------------------------------------
# Main prompt builder
# ---------------------------------------------------------------------------
 
def build_evaluation_prompt(
    candidate: dict[str, Any],
    job: dict[str, Any],
    match_result: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """
    Build a (system_prompt, user_prompt) tuple ready to send to OpenAI.
 
    Parameters
    ----------
    candidate    : Candidate profile dictionary.
    job          : Job requirement dictionary.
    match_result : Optional pre-computed match signals (overlap_skills,
                   missing_skills, score) to enrich the prompt.
 
    Returns
    -------
    (system_prompt, user_prompt)
    """
    candidate_block = build_candidate_block(candidate)
    job_block       = build_job_block(job)
 
    # Optional match-signal block
    if match_result:
        overlap  = _list_block(match_result.get("overlap_skills", []))
        missing  = _list_block(match_result.get("missing_skills", []))
        pre_score = match_result.get("score", None)
        pre_score_line = (
            f"  Pre-computed match score : {pre_score}/100\n" if pre_score is not None else ""
        )
        match_block = (
            f"\nPRE-COMPUTED MATCH SIGNALS\n"
            f"{pre_score_line}"
            f"{_section('Overlapping Skills', overlap)}\n\n"
            f"{_section('Missing Skills', missing)}\n"
        )
    else:
        match_block = ""
 
    user_prompt = f"""\
Below is a candidate profile and a job description. Analyse them thoroughly and
produce the evaluation report in EXACTLY the format shown.
 
{'='*68}
{candidate_block}
{'='*68}
{job_block}
{match_block}{'='*68}
 
OUTPUT FORMAT (follow this exactly — no extra prose outside the sections):
 
## Candidate Evaluation Report
 
**Candidate:** <full name>
**Role Applied:** <job title> at <company>
 
---
 
### Overall Score
**Score: <0-100>/100**
 
(One sentence verdict, e.g., "Strong candidate with minor skill gaps.")
 
---
 
### Candidate Summary
<2-3 sentence professional summary of the candidate in context of the role.>
 
---
 
### Strengths
- <Strength 1 with brief justification>
- <Strength 2 with brief justification>
- <Strength 3 with brief justification>
(add more if warranted, keep each bullet concise)
 
---
 
### Weaknesses / Gaps
- <Weakness 1 with brief note on impact>
- <Weakness 2 with brief note on impact>
(add more if warranted; write "None identified." if truly none)
 
---
 
### Recommendations for the Recruiter
1. <Actionable recommendation 1>
2. <Actionable recommendation 2>
3. <Actionable recommendation 3>
(add more as needed)
 
---
 
### Hiring Recommendation
**Verdict:** <Strongly Recommend | Recommend | Conditional Recommend | Do Not Recommend>
<One sentence rationale.>
"""
 
    return SYSTEM_PROMPT, user_prompt
 
 
# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sample_candidate = {
        "name": "Hadeed Hassan",
        "email": "hadeed@example.com",
        "years_experience": 3,
        "education": ["BS Information Technology — Quaid-i-Azam University (2024)"],
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
 
    sys_p, user_p = build_evaluation_prompt(sample_candidate, sample_job, sample_match)
    print("=== SYSTEM PROMPT ===")
    print(sys_p)
    print("\n=== USER PROMPT ===")
    print(user_p)