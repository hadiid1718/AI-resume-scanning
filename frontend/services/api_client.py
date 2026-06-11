from __future__ import annotations

from pathlib import Path
import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout


class APIError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class APIClient:
    def __init__(self, base_url: str, timeout: int = 60) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _handle_response(self, response: requests.Response) -> dict:
        try:
            response.raise_for_status()
        except HTTPError as exc:
            detail = response.text[:300] if response.text else str(exc)
            raise APIError(f"Request failed ({response.status_code}): {detail}", response.status_code) from exc
        if not response.content:
            return {}
        return response.json()

    def health(self) -> dict:
        try:
            response = requests.get(self._url("/api/v1/health"), timeout=5)
            return self._handle_response(response)
        except ConnectionError as exc:
            raise APIError("Cannot reach backend. Is the API server running?") from exc
        except Timeout as exc:
            raise APIError("Backend health check timed out.") from exc

    def upload_resume(self, file_bytes: bytes, filename: str, content_type: str) -> dict:
        try:
            response = requests.post(
                self._url("/api/v1/resumes/upload"),
                files={"file": (filename, file_bytes, content_type)},
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except ConnectionError as exc:
            raise APIError("Cannot reach backend for resume upload.") from exc
        except Timeout as exc:
            raise APIError("Resume upload timed out.") from exc

    def parse_resume(self, resume_text: str) -> dict:
        return self._post_json("/api/v1/resumes/parse", {"resume_text": resume_text})

    def extract_candidate(self, resume_text: str) -> dict:
        return self._post_json("/api/v1/candidates/extract", {"resume_text": resume_text})

    def extract_skills(self, resume_text: str) -> dict:
        return self._post_json("/api/v1/skills/extract", {"resume_text": resume_text})

    def parse_job(self, title: str, description: str) -> dict:
        return self._post_json("/api/v1/jobs/parse", {"title": title, "description": description})

    def match(self, candidate_skills: list, job_skills: list) -> dict:
        return self._post_json(
            "/api/v1/match",
            {"candidate_skills": candidate_skills, "job_skills": job_skills},
        )

    def rank(self, match_result: dict) -> dict:
        return self._post_json("/api/v1/rank", match_result)

    def evaluate(self, candidate: dict, job: dict, match_result: dict) -> dict:
        return self._post_json(
            "/api/v1/evaluate",
            {"candidate": candidate, "job": job, "match_result": match_result},
        )

    def generate_report(self, payload: dict) -> dict:
        return self._post_json("/api/v1/report", payload)

    def analyze(
        self,
        resume_text: str,
        job_title: str,
        job_description: str,
    ) -> dict:
        try:
            response = requests.post(
                self._url("/api/v1/analyze"),
                data={
                    "resume_text": resume_text,
                    "job_title": job_title,
                    "job_description": job_description,
                },
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except ConnectionError as exc:
            raise APIError("Cannot reach backend for analysis.") from exc
        except Timeout as exc:
            raise APIError("Analysis timed out. Try a shorter resume or increase timeout.") from exc

    def ai_evaluate(self, candidate: dict, job: dict, match_result: dict | None = None) -> dict:
        payload = {"candidate": candidate, "job": job}
        if match_result:
            payload["match_result"] = match_result
        return self._post_json("/api/v1/ai/evaluate", payload)

    def ai_evaluate_batch(self, candidates: list[dict]) -> dict:
        return self._post_json("/api/v1/ai/evaluate/batch", {"candidates": candidates})

    def analyze_batch(
        self,
        resume_texts: list[str],
        job_title: str,
        job_description: str,
    ) -> dict:
        return self._post_json(
            "/api/v1/analyze/batch",
            {
                "resume_texts": resume_texts,
                "job_title": job_title,
                "job_description": job_description,
            },
        )

    def get_rankings(self, limit: int = 100) -> dict:
        try:
            response = requests.get(
                self._url("/api/v1/rankings"),
                params={"limit": limit},
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except ConnectionError as exc:
            raise APIError("Cannot reach backend for rankings.") from exc

    def _post_json(self, path: str, payload: dict) -> dict:
        try:
            response = requests.post(
                self._url(path),
                json=payload,
                timeout=self.timeout,
            )
            return self._handle_response(response)
        except ConnectionError as exc:
            raise APIError(f"Cannot reach backend at {path}.") from exc
        except Timeout as exc:
            raise APIError(f"Request to {path} timed out.") from exc


def extract_text_from_file(filename: str, file_bytes: bytes) -> str:
    """Extract resume text locally without importing backend modules."""
    from frontend.utils.file_extract import FileExtractionError, extract_text_from_bytes

    try:
        return extract_text_from_bytes(filename, file_bytes)
    except FileExtractionError as exc:
        raise APIError(str(exc)) from exc
