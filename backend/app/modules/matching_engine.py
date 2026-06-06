class MatchingEngine:
    def match(self, candidate: dict, job: dict) -> dict:
        candidate_skills = set(candidate.get("skills", []))
        job_skills = set(job.get("skills", []))
        overlap = sorted(candidate_skills & job_skills)
        union = candidate_skills | job_skills
        skill_score = round((len(overlap) / len(union)) * 100, 2) if union else 0.0

        return {
            "score": skill_score,
            "overlap_skills": overlap,
            "missing_skills": sorted(job_skills - candidate_skills),
        }
