"""Tests for JobSearchAgent."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from src.agents.job_search_agent import JobSearchAgent, _build_queries, _parse_json_array
from src.models import JobRole, ResumeData


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _make_llm_response(payload) -> MagicMock:
    response = MagicMock()
    response.content = json.dumps(payload)
    return response


_JOB_LIST_PAYLOAD = [
    {
        "title": "Staff Engineer",
        "company": "TechCorp",
        "location": "Remote",
        "url": "https://example.com/job/1",
        "description": "Build distributed systems.",
        "match_score": 0.90,
        "source": "tavily",
    },
    {
        "title": "Senior Python Developer",
        "company": "DataCo",
        "location": "NYC",
        "url": "https://example.com/job/2",
        "description": "Data pipeline development.",
        "match_score": 0.75,
        "source": "tavily",
    },
]

_SEARCH_RESULTS = [
    {
        "title": "Staff Engineer at TechCorp",
        "url": "https://example.com/job/1",
        "content": "TechCorp is hiring a Staff Engineer to build distributed systems.",
    }
]


# ---------------------------------------------------------------------------
# Tests for helpers
# ---------------------------------------------------------------------------

class TestBuildQueries:
    def test_uses_target_roles(self, sample_resume_data):
        queries = _build_queries(sample_resume_data)
        assert len(queries) >= 1
        assert any("Staff Software Engineer" in q or "Principal Engineer" in q for q in queries)

    def test_falls_back_to_current_role(self):
        resume = ResumeData(parsed_text="x", current_role="Data Analyst", target_roles=[])
        queries = _build_queries(resume)
        assert any("Data Analyst" in q for q in queries)

    def test_fallback_when_no_roles(self):
        resume = ResumeData(parsed_text="x")
        queries = _build_queries(resume)
        assert len(queries) >= 1


class TestParseJsonArray:
    def test_plain_json_array(self):
        result = _parse_json_array(json.dumps(_JOB_LIST_PAYLOAD))
        assert len(result) == 2

    def test_markdown_fenced(self):
        text = f"```json\n{json.dumps(_JOB_LIST_PAYLOAD)}\n```"
        result = _parse_json_array(text)
        assert len(result) == 2

    def test_embedded_in_text(self):
        text = f"Here are jobs: {json.dumps(_JOB_LIST_PAYLOAD)}"
        result = _parse_json_array(text)
        assert len(result) == 2

    def test_invalid_returns_empty(self):
        result = _parse_json_array("no json here")
        assert result == []


# ---------------------------------------------------------------------------
# Tests for JobSearchAgent
# ---------------------------------------------------------------------------

class TestJobSearchAgent:
    def test_returns_list_of_job_roles(
        self, sample_resume_data, mock_llm, mock_search_client
    ):
        mock_search_client.search_jobs.return_value = _SEARCH_RESULTS
        mock_llm.invoke.return_value = _make_llm_response(_JOB_LIST_PAYLOAD)

        agent = JobSearchAgent(llm=mock_llm, search_client=mock_search_client)
        result = agent.search_jobs(sample_resume_data)

        assert isinstance(result, list)
        assert all(isinstance(j, JobRole) for j in result)
        assert len(result) == 2

    def test_empty_search_returns_empty_list(
        self, sample_resume_data, mock_llm, mock_search_client
    ):
        mock_search_client.search_jobs.return_value = []
        agent = JobSearchAgent(llm=mock_llm, search_client=mock_search_client)
        result = agent.search_jobs(sample_resume_data)
        assert result == []

    def test_results_sorted_by_match_score(
        self, sample_resume_data, mock_llm, mock_search_client
    ):
        mock_search_client.search_jobs.return_value = _SEARCH_RESULTS
        mock_llm.invoke.return_value = _make_llm_response(_JOB_LIST_PAYLOAD)

        agent = JobSearchAgent(llm=mock_llm, search_client=mock_search_client)
        result = agent.search_jobs(sample_resume_data)

        scores = [j.match_score for j in result]
        assert scores == sorted(scores, reverse=True)

    def test_llm_invalid_response_returns_empty(
        self, sample_resume_data, mock_llm, mock_search_client
    ):
        mock_search_client.search_jobs.return_value = _SEARCH_RESULTS
        # LLM returns garbage
        mock_llm.invoke.return_value = _make_llm_response("not an array")

        agent = JobSearchAgent(llm=mock_llm, search_client=mock_search_client)
        result = agent.search_jobs(sample_resume_data)
        # Should not crash; returns empty or partial results
        assert isinstance(result, list)

    def test_search_client_called_at_least_once(
        self, sample_resume_data, mock_llm, mock_search_client
    ):
        mock_search_client.search_jobs.return_value = []
        agent = JobSearchAgent(llm=mock_llm, search_client=mock_search_client)
        agent.search_jobs(sample_resume_data)
        assert mock_search_client.search_jobs.call_count >= 1

    def test_match_scores_within_bounds(
        self, sample_resume_data, mock_llm, mock_search_client
    ):
        mock_search_client.search_jobs.return_value = _SEARCH_RESULTS
        # Payload with out-of-range scores
        payload = [
            {**_JOB_LIST_PAYLOAD[0], "match_score": 1.5},
            {**_JOB_LIST_PAYLOAD[1], "match_score": -0.2},
        ]
        mock_llm.invoke.return_value = _make_llm_response(payload)

        agent = JobSearchAgent(llm=mock_llm, search_client=mock_search_client)
        result = agent.search_jobs(sample_resume_data)

        for job in result:
            assert 0.0 <= job.match_score <= 1.0
