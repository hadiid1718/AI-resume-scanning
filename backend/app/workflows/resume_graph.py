"""LangGraph-orchestrated resume screening pipeline."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from backend.app.modules.recommendation import extract_ai_score, score_to_recommendation
from backend.app.workflows.state import ResumePipelineState


class ResumeGraphWorkflow:
    """Orchestrates parse -> extract -> match -> Gemini evaluate -> rank -> report."""

    def __init__(self, pipeline: Any) -> None:
        self.pipeline = pipeline
        self._gemini_extractor = None
        self._gemini_evaluator = None
        self._init_gemini_services()
        self.app = self._build_graph()

    def _init_gemini_services(self) -> None:
        try:
            from backend.app.services.gemini_extractor import GeminiResumeExtractor

            self._gemini_extractor = GeminiResumeExtractor()
        except EnvironmentError:
            self._gemini_extractor = None
        try:
            from backend.app.services.ai_evaluator import AIEvaluationEngine

            self._gemini_evaluator = AIEvaluationEngine()
        except EnvironmentError:
            self._gemini_evaluator = None

    def _build_graph(self):
        graph = StateGraph(ResumePipelineState)

        graph.add_node("parse_resume", self._parse_resume)
        graph.add_node("extract_candidate", self._extract_candidate)
        graph.add_node("parse_job", self._parse_job)
        graph.add_node("match", self._match)
        graph.add_node("evaluate", self._evaluate)
        graph.add_node("rank", self._rank)
        graph.add_node("report", self._report)

        graph.set_entry_point("parse_resume")
        graph.add_edge("parse_resume", "extract_candidate")
        graph.add_edge("extract_candidate", "parse_job")
        graph.add_edge("parse_job", "match")
        graph.add_edge("match", "evaluate")
        graph.add_edge("evaluate", "rank")
        graph.add_edge("rank", "report")
        graph.add_edge("report", END)

        return graph.compile()

    def run(self, resume_text: str, job_title: str, job_description: str) -> dict[str, Any]:
        initial: ResumePipelineState = {
            "resume_text": resume_text,
            "job_title": job_title,
            "job_description": job_description,
            "status": "started",
            "error": None,
        }
        final_state = self.app.invoke(initial)
        return self._to_payload(final_state)

    def run_batch(
        self,
        resumes: list[str],
        job_title: str,
        job_description: str,
    ) -> dict[str, Any]:
        results = [self.run(text, job_title, job_description) for text in resumes]
        ranked = self.pipeline.ranking_engine.rank_candidates(
            [
                {
                    "candidate_name": r["candidate"].get("full_name"),
                    "score": extract_ai_score(r),
                    **r.get("ai_evaluation", {}),
                    **r.get("match_result", {}),
                }
                for r in results
            ]
        )
        return {
            "results": results,
            "ranked_candidates": ranked,
            "total": len(results),
        }

    def _parse_resume(self, state: ResumePipelineState) -> ResumePipelineState:
        parsed = self.pipeline.resume_parser.parse_text(state["resume_text"])
        return {"parsed_resume": parsed, "status": "parsed"}

    def _extract_candidate(self, state: ResumePipelineState) -> ResumePipelineState:
        candidate = self.pipeline.candidate_extractor.extract(state["parsed_resume"])
        candidate.update(self.pipeline.skill_engine.extract(state["resume_text"]))
        if self._gemini_extractor:
            try:
                gemini_data = self._gemini_extractor.extract(state["resume_text"])
                for key, value in gemini_data.items():
                    if value not in (None, "", [], {}):
                        candidate[key] = value
            except Exception:
                pass
        return {"candidate": candidate, "status": "extracted"}

    def _parse_job(self, state: ResumePipelineState) -> ResumePipelineState:
        job = self.pipeline.job_parser.parse(state["job_title"], state["job_description"])
        return {"job": job, "status": "job_parsed"}

    def _match(self, state: ResumePipelineState) -> ResumePipelineState:
        match_result = self.pipeline.matching_engine.match(state["candidate"], state["job"])
        return {"match_result": match_result, "status": "matched"}

    def _evaluate(self, state: ResumePipelineState) -> ResumePipelineState:
        candidate = state["candidate"]
        job = state["job"]
        match_result = state["match_result"]

        if self._gemini_evaluator:
            try:
                ai_evaluation = self._gemini_evaluator.evaluate(candidate, job, match_result)
            except Exception:
                ai_evaluation = self.pipeline.evaluation_engine.evaluate(candidate, job, match_result)
        else:
            ai_evaluation = self.pipeline.evaluation_engine.evaluate(candidate, job, match_result)

        evaluation = {
            "score": ai_evaluation.get("score", match_result.get("score", 0)),
            "overall_assessment": ai_evaluation.get("overall_assessment", ""),
            "summary": ai_evaluation.get("summary", ""),
            "strengths": ai_evaluation.get("strengths", []),
            "gaps": ai_evaluation.get("weaknesses", ai_evaluation.get("gaps", [])),
            "weaknesses": ai_evaluation.get("weaknesses", []),
            "recommendations": ai_evaluation.get("recommendations", []),
            "skills_analysis": ai_evaluation.get("skills_analysis", ""),
            "experience_analysis": ai_evaluation.get("experience_analysis", ""),
            "education_analysis": ai_evaluation.get("education_analysis", ""),
            "verdict": ai_evaluation.get("verdict", ""),
        }
        ai_score = int(ai_evaluation.get("score", match_result.get("score", 0)))
        recommendation = score_to_recommendation(ai_score)
        return {
            "ai_evaluation": ai_evaluation,
            "evaluation": evaluation,
            "ai_score": ai_score,
            "recommendation": recommendation,
            "status": "evaluated",
        }

    def _rank(self, state: ResumePipelineState) -> ResumePipelineState:
        rank_input = {
            "score": state.get("ai_score", state["match_result"].get("score", 0)),
            **state["match_result"],
        }
        rank_result = self.pipeline.ranking_engine.rank(rank_input)
        rank_result["recommendation"] = state.get("recommendation")
        return {"rank_result": rank_result, "status": "ranked"}

    def _report(self, state: ResumePipelineState) -> ResumePipelineState:
        report = self.pipeline.report_generator.build(
            {
                "candidate": state["candidate"],
                "job": state["job"],
                "match_result": state["match_result"],
                "rank_result": state["rank_result"],
                "evaluation": state["evaluation"],
                "ai_evaluation": state.get("ai_evaluation"),
                "recommendation": state.get("recommendation"),
            }
        )
        return {"report": report, "status": "completed"}

    @staticmethod
    def _to_payload(state: ResumePipelineState) -> dict[str, Any]:
        return {
            "parsed_resume": state.get("parsed_resume"),
            "candidate": state.get("candidate"),
            "job": state.get("job"),
            "match_result": state.get("match_result"),
            "ai_evaluation": state.get("ai_evaluation"),
            "rank_result": state.get("rank_result"),
            "evaluation": state.get("evaluation"),
            "report": state.get("report"),
            "ai_score": state.get("ai_score"),
            "recommendation": state.get("recommendation"),
            "status": state.get("status"),
        }
