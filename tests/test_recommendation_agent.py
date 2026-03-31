"""Tests for RecommendationAgent."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from langchain_core.messages import AIMessage

from src.agents.recommendation_agent import (
    RECOMMENDATION_TOOLS,
    RecommendationAgent,
    _parse_json_array,
    compute_skill_overlap,
    create_recommendation_agent,
    format_candidate_profile,
)
from src.models import JobRole, ResumeData


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def _make_agent_response(payload) -> dict:
    return {"messages": [AIMessage(content=json.dumps(payload))]}


# ---------------------------------------------------------------------------
# Tests for tools
# ---------------------------------------------------------------------------

class TestRecommendationTools:
    def test_tools_registered(self):
        assert compute_skill_overlap in RECOMMENDATION_TOOLS
        assert format_candidate_profile in RECOMMENDATION_TOOLS

    def test_compute_skill_overlap_matches(self):
        skills = json.dumps(["Python", "Docker", "Kubernetes"])
        desc = "We need Python and Kubernetes experience."
        result = json.loads(compute_skill_overlap.invoke({"candidate_skills_json": skills, "job_description": desc}))
        assert result["overlap_count"] == 2
        assert "Python" in result["matching_skills"]
        assert "Kubernetes" in result["matching_skills"]

    def test_compute_skill_overlap_no_match(self):
        skills = json.dumps(["Java", "Spring"])
        desc = "Python and Go required."
        result = json.loads(compute_skill_overlap.invoke({"candidate_skills_json": skills, "job_description": desc}))
        assert result["overlap_count"] == 0

    def test_compute_skill_overlap_invalid_json(self):
        result = json.loads(compute_skill_overlap.invoke({"candidate_skills_json": "not-json", "job_description": "Python"}))
        assert result["overlap_count"] == 0

    def test_format_candidate_profile_returns_string(self):
        data = {
            "current_role": "Engineer",
            "experience_years": 5,
            "skills": ["Python", "Go"],
            "education": ["B.Sc. CS"],
            "target_roles": ["Staff Engineer"],
        }
        result = format_candidate_profile.invoke({"resume_data_json": json.dumps(data)})
        assert "Engineer" in result
        assert "Python" in result
        assert "Staff Engineer" in result

    def test_format_candidate_profile_invalid_json(self):
        result = format_candidate_profile.invoke({"resume_data_json": "not-json"})
        assert isinstance(result, str)

    def test_create_recommendation_agent_returns_graph(self):
        mock_llm = MagicMock()
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)
        agent = create_recommendation_agent(mock_llm)
        assert hasattr(agent, "invoke")


# ---------------------------------------------------------------------------
# Tests for RecommendationAgent
# ---------------------------------------------------------------------------

class TestRecommendationAgent:
    def test_returns_list_of_job_roles(self, sample_resume_data, sample_job_roles):
        agent = RecommendationAgent(llm=MagicMock())
        mock_internal = MagicMock()
        mock_internal.invoke.return_value = _make_agent_response(_RECOMMEND_PAYLOAD)
        agent._agent = mock_internal

        result = agent.recommend_roles(sample_resume_data, sample_job_roles)

        assert isinstance(result, list)
        assert all(isinstance(r, JobRole) for r in result)
        assert len(result) <= 5  # default max_shortlisted_jobs

    def test_results_sorted_by_match_score(self, sample_resume_data, sample_job_roles):
        agent = RecommendationAgent(llm=MagicMock())
        mock_internal = MagicMock()
        mock_internal.invoke.return_value = _make_agent_response(_RECOMMEND_PAYLOAD)
        agent._agent = mock_internal

        result = agent.recommend_roles(sample_resume_data, sample_job_roles)

        scores = [r.match_score for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_reasoning_field_populated(self, sample_resume_data, sample_job_roles):
        agent = RecommendationAgent(llm=MagicMock())
        mock_internal = MagicMock()
        mock_internal.invoke.return_value = _make_agent_response(_RECOMMEND_PAYLOAD)
        agent._agent = mock_internal

        result = agent.recommend_roles(sample_resume_data, sample_job_roles)

        assert result[0].reasoning != ""

    def test_empty_jobs_returns_empty(self, sample_resume_data):
        agent = RecommendationAgent(llm=MagicMock())
        mock_internal = MagicMock()
        agent._agent = mock_internal

        result = agent.recommend_roles(sample_resume_data, [])
        assert result == []
        mock_internal.invoke.assert_not_called()

    def test_agent_garbage_response_falls_back_to_score_sort(
        self, sample_resume_data, sample_job_roles
    ):
        """If agent returns garbage, fallback to sorting by existing match_score."""
        agent = RecommendationAgent(llm=MagicMock())
        mock_internal = MagicMock()
        mock_internal.invoke.return_value = _make_agent_response("not-an-array")
        agent._agent = mock_internal

        result = agent.recommend_roles(sample_resume_data, sample_job_roles)

        assert len(result) > 0
        scores = [r.match_score for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_top_n_respected(self, sample_resume_data, sample_job_roles):
        """top_n parameter should cap the result list."""
        big_payload = _RECOMMEND_PAYLOAD * 5  # 10 items
        agent = RecommendationAgent(llm=MagicMock())
        mock_internal = MagicMock()
        mock_internal.invoke.return_value = _make_agent_response(big_payload)
        agent._agent = mock_internal

        result = agent.recommend_roles(sample_resume_data, sample_job_roles, top_n=2)
        assert len(result) <= 2

    def test_agent_called_with_candidate_info(self, sample_resume_data, sample_job_roles):
        """Agent invoke messages should include candidate role info."""
        agent = RecommendationAgent(llm=MagicMock())
        mock_internal = MagicMock()
        mock_internal.invoke.return_value = _make_agent_response(_RECOMMEND_PAYLOAD)
        agent._agent = mock_internal

        agent.recommend_roles(sample_resume_data, sample_job_roles)

        call_args = mock_internal.invoke.call_args
        messages = call_args[0][0]["messages"]
        combined_text = " ".join(str(m.content) for m in messages)
        assert "Senior Software Engineer" in combined_text or "experience" in combined_text.lower()
