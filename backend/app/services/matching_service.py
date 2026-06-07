from __future__ import annotations
import argparse
import json
import sys
from typing import Optional
 
from matching_engine import MatchingEngine, MatchReport
 
 
# ──────────────────────────────────────────────
# Score Tier
# ──────────────────────────────────────────────
 
def score_tier(score: float) -> str:
    if score >= 85:
        return "Excellent ★★★"
    elif score >= 70:
        return "Good      ★★☆"
    elif score >= 50:
        return "Moderate  ★☆☆"
    else:
        return "Poor      ☆☆☆"
 
 
# ──────────────────────────────────────────────
# Service
# ──────────────────────────────────────────────
 
class MatchingService:
    """
    Orchestrates MatchingEngine calls and surfaces higher-level features.
 
    Usage
    -----
    service = MatchingService()
    report  = service.match_one(candidate, job)
    print(report.summary())
 
    ranked = service.rank_candidates([c1, c2, c3], job)
    for rank, (score, name) in enumerate(ranked, 1):
        print(f"#{rank}  {name}  –  {score:.1f}%")
    """
 
    def __init__(
        self,
        skill_weight: float = 0.50,
        experience_weight: float = 0.30,
        education_weight: float = 0.20,
    ) -> None:
        self.engine = MatchingEngine(skill_weight, experience_weight, education_weight)
 
    # ── single match ────────────────────────────
 
    def match_one(self, candidate: dict, job: dict) -> MatchReport:
        """Return a full MatchReport for one candidate vs one job."""
        return self.engine.match(candidate, job)
 
    # ── batch ranking ───────────────────────────
 
    def rank_candidates(
        self, candidates: list[dict], job: dict
    ) -> list[tuple[float, str, MatchReport]]:
        """
        Match every candidate against the job and return a ranked list.
 
        Returns
        -------
        list of (overall_score, candidate_name, MatchReport)
        sorted descending by score.
        """
        results = []
        for c in candidates:
            report = self.engine.match(c, job)
            results.append((report.overall_score, c.get("name", "?"), report))
        results.sort(key=lambda x: x[0], reverse=True)
        return results
 
    # ── pretty rank table ───────────────────────
 
    def ranking_table(self, candidates: list[dict], job: dict) -> str:
        ranked = self.rank_candidates(candidates, job)
        header = (
            f"\n{'═'*65}\n"
            f"  CANDIDATE RANKING  –  {job.get('title', 'Unknown Role')}\n"
            f"{'═'*65}\n"
            f"  {'#':<4} {'Name':<25} {'Score':>7}  {'Skill':>7}  {'Exp':>6}  {'Edu':>6}  Tier\n"
            f"{'─'*65}"
        )
        rows = [header]
        for rank, (score, name, report) in enumerate(ranked, 1):
            rows.append(
                f"  {rank:<4} {name:<25} {score:>6.1f}%"
                f"  {report.skill.match_percent:>6.1f}%"
                f"  {report.experience.match_percent:>5.1f}%"
                f"  {report.education.match_percent:>5.1f}%"
                f"  {score_tier(score)}"
            )
        rows.append("═" * 65)
        return "\n".join(rows)
 
    # ── JSON export ─────────────────────────────
 
    @staticmethod
    def to_dict(report: MatchReport) -> dict:
        """Serialise a MatchReport to a plain dict (JSON-safe)."""
        return {
            "candidate_name": report.candidate_name,
            "job_title": report.job_title,
            "overall_score": report.overall_score,
            "tier": score_tier(report.overall_score),
            "skill": {
                "required": report.skill.required,
                "found": report.skill.found,
                "missing": report.skill.missing,
                "match_percent": report.skill.match_percent,
            },
            "experience": {
                "required_years": report.experience.required_years,
                "candidate_years": report.experience.candidate_years,
                "match_percent": report.experience.match_percent,
                "note": report.experience.note,
            },
            "education": {
                "required_level": report.education.required_level,
                "candidate_level": report.education.candidate_level,
                "match_percent": report.education.match_percent,
                "note": report.education.note,
            },
        }
 
 
# ──────────────────────────────────────────────
# CLI Entry Point  (fully dynamic — no hardcoded data)
# ──────────────────────────────────────────────
 
def _load_json(path: str) -> object:
    """Load JSON from a file path, or raise a clear error."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        sys.exit(f"[ERROR] File not found: {path}")
    except json.JSONDecodeError as exc:
        sys.exit(f"[ERROR] Invalid JSON in {path}: {exc}")
 
 
def _validate_job(job: dict) -> None:
    required_keys = {"title", "required_skills", "required_experience_years", "required_education"}
    missing = required_keys - job.keys()
    if missing:
        sys.exit(f"[ERROR] job.json missing keys: {missing}")
 
 
def _validate_candidates(candidates: list) -> None:
    if not isinstance(candidates, list) or len(candidates) == 0:
        sys.exit("[ERROR] candidates.json must be a non-empty list.")
    required_keys = {"name", "skills", "experience_years", "education"}
    for i, c in enumerate(candidates):
        missing = required_keys - c.keys()
        if missing:
            sys.exit(f"[ERROR] Candidate #{i+1} missing keys: {missing}")
 
 
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Resume Matching Engine — compare candidates against a job spec."
    )
    parser.add_argument("--job",        required=True, help="Path to job spec JSON file")
    parser.add_argument("--candidates", required=True, help="Path to candidates JSON file (list)")
    parser.add_argument("--out",        default=None,  help="Optional path to write JSON results")
    parser.add_argument(
        "--weights", nargs=3, type=float, metavar=("SKILL", "EXP", "EDU"),
        default=[0.50, 0.30, 0.20],
        help="Scoring weights for skill / experience / education (must sum to 1.0)"
    )
    args = parser.parse_args()
 
    # ── load & validate ──────────────────────────
    job        = _load_json(args.job)
    candidates = _load_json(args.candidates)
    _validate_job(job)
    _validate_candidates(candidates)
 
    # ── run matching ─────────────────────────────
    sw, ew, edw = args.weights
    service = MatchingService(skill_weight=sw, experience_weight=ew, education_weight=edw)
 
    # Ranking table
    print(service.ranking_table(candidates, job))
 
    # Detailed report per candidate
    all_results = []
    for candidate in candidates:
        report = service.match_one(candidate, job)
        print(report.summary())
        all_results.append(service.to_dict(report))
 
    # ── optional JSON output ─────────────────────
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(all_results, fh, indent=2)
        print(f"\n  Results written to: {args.out}")
 
 
if __name__ == "__main__":
    main()