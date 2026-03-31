"""Tests for RecommendationAgent."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from src.agents.recommendation_agent import RecommendationAgent
from src.models import JobRole, ResumeData


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_llm_response(payload) -> MagicMock:
    response = MagicMock()
    response.content = json.dumps(payload)
    return response


_RECOMMEND_PAYLOAD = [
    {
        "title": "Staff Software Engineer",
        "company": "TechCorp",
        "location": "Remote",
        "url": "https://example.com/1",
        "description": "Lead distributed systems work.",
        "match_score": 0.95,
        "source": "tavily",
        "reasoning": "Excellent fit: Python, Kubernetes, 7 years experience.",
    },
    {
        "title": "Principal Engineer",
        "company": "CloudCo",
        "location": "NYC",
        "url": "https://example.com/2",
        "description": "Architect cloud solutions.",
        "match_score": 0.88,
        "source": "tavily",
        "reasoning": "AWS expertise aligns well.",
    },
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRecommendationAgent:
    def test_returns_list_of_job_roles(self, sample_resume_data, sample_job_roles, mock_llm):
        mock_llm.invoke.return_value = _make_llm_response(_RECOMMEND_PAYLOAD)
        agent = RecommendationAgent(llm=mock_llm)
        result = agent.recommend_roles(sample_resume_data, sample_job_roles)

        assert isinstance(result, list)
        assert all(isinstance(r, JobRole) for r in result)
        assert len(result) <= 5  # default max_shortlisted_jobs

    def test_results_sorted_by_match_score(self, sample_resume_data, sample_job_roles, mock_llm):
        mock_llm.invoke.return_value = _make_llm_response(_RECOMMEND_PAYLOAD)
        agent = RecommendationAgent(llm=mock_llm)
        result = agent.recommend_roles(sample_resume_data, sample_job_roles)

        scores = [r.match_score for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_reasoning_field_populated(self, sample_resume_data, sample_job_roles, mock_llm):
        mock_llm.invoke.return_value = _make_llm_response(_RECOMMEND_PAYLOAD)
        agent = RecommendationAgent(llm=mock_llm)
        result = agent.recommend_roles(sample_resume_data, sample_job_roles)

        assert result[0].reasoning != ""

    def test_empty_jobs_returns_empty(self, sample_resume_data, mock_llm):
        agent = RecommendationAgent(llm=mock_llm)
        result = agent.recommend_roles(sample_resume_data, [])
        assert result == []
        mock_llm.invoke.assert_not_called()

    def test_llm_garbage_response_falls_back_to_score_sort(
        self, sample_resume_data, sample_job_roles, mock_llm
    ):
        """If LLM returns garbage, fallback to sorting by existing match_score."""
        mock_llm.invoke.return_value = _make_llm_response("not-an-array")
        agent = RecommendationAgent(llm=mock_llm)
        result = agent.recommend_roles(sample_resume_data, sample_job_roles)

        assert len(result) > 0
        scores = [r.match_score for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_top_n_respected(self, sample_resume_data, sample_job_roles, mock_llm):
        """top_n parameter should cap the result list."""
        big_payload = _RECOMMEND_PAYLOAD * 5  # 10 items
        mock_llm.invoke.return_value = _make_llm_response(big_payload)
        agent = RecommendationAgent(llm=mock_llm)
        result = agent.recommend_roles(sample_resume_data, sample_job_roles, top_n=2)
        assert len(result) <= 2

    def test_llm_called_with_candidate_info(self, sample_resume_data, sample_job_roles, mock_llm):
        """LLM messages should include candidate role info."""
        mock_llm.invoke.return_value = _make_llm_response(_RECOMMEND_PAYLOAD)
        agent = RecommendationAgent(llm=mock_llm)
        agent.recommend_roles(sample_resume_data, sample_job_roles)

        call_args = mock_llm.invoke.call_args
        messages = call_args[0][0]
        combined_text = " ".join(str(m.content) for m in messages)
        assert "Senior Software Engineer" in combined_text or "experience" in combined_text.lower()
