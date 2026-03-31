"""Tests for JobSearchAgent."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from langchain_core.messages import AIMessage

from src.agents.job_search_agent import (
    JobSearchAgent,
    _build_queries,
    _parse_json_array,
    create_job_search_agent,
    make_search_jobs_tool,
)
from src.models import JobRole, ResumeData


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

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


def _make_agent_response(payload) -> dict:
    """Build a mock LangGraph agent result with the final AI message."""
    return {"messages": [AIMessage(content=json.dumps(payload))]}


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
# Tests for the search_jobs_online tool
# ---------------------------------------------------------------------------

class TestSearchJobsTool:
    def test_tool_calls_search_client(self, mock_search_client):
        """search_jobs_online tool should delegate to the search client."""
        mock_search_client.search_jobs.return_value = _SEARCH_RESULTS
        search_tool = make_search_jobs_tool(mock_search_client, max_results_per_query=5)

        result = search_tool.invoke({"query": "Python engineer remote"})

        mock_search_client.search_jobs.assert_called_once_with(
            "Python engineer remote", max_results=5
        )
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 1

    def test_tool_returns_empty_on_no_results(self, mock_search_client):
        mock_search_client.search_jobs.return_value = []
        search_tool = make_search_jobs_tool(mock_search_client)
        result = search_tool.invoke({"query": "some query"})
        assert json.loads(result) == []

    def test_create_job_search_agent_returns_graph(self, mock_search_client):
        mock_llm = MagicMock()
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)
        agent = create_job_search_agent(mock_llm, mock_search_client, max_results=10)
        assert hasattr(agent, "invoke")


# ---------------------------------------------------------------------------
# Tests for JobSearchAgent
# ---------------------------------------------------------------------------

class TestJobSearchAgent:
    def test_returns_list_of_job_roles(self, sample_resume_data, mock_search_client):
        agent = JobSearchAgent(llm=MagicMock(), search_client=mock_search_client)
        mock_internal = MagicMock()
        mock_internal.invoke.return_value = _make_agent_response(_JOB_LIST_PAYLOAD)
        agent._agent = mock_internal

        result = agent.search_jobs(sample_resume_data)

        assert isinstance(result, list)
        assert all(isinstance(j, JobRole) for j in result)
        assert len(result) == 2

    def test_empty_agent_response_returns_empty_list(self, sample_resume_data, mock_search_client):
        agent = JobSearchAgent(llm=MagicMock(), search_client=mock_search_client)
        mock_internal = MagicMock()
        mock_internal.invoke.return_value = _make_agent_response([])
        agent._agent = mock_internal

        result = agent.search_jobs(sample_resume_data)
        assert result == []

    def test_results_sorted_by_match_score(self, sample_resume_data, mock_search_client):
        agent = JobSearchAgent(llm=MagicMock(), search_client=mock_search_client)
        mock_internal = MagicMock()
        mock_internal.invoke.return_value = _make_agent_response(_JOB_LIST_PAYLOAD)
        agent._agent = mock_internal

        result = agent.search_jobs(sample_resume_data)

        scores = [j.match_score for j in result]
        assert scores == sorted(scores, reverse=True)

    def test_invalid_agent_response_returns_empty(self, sample_resume_data, mock_search_client):
        agent = JobSearchAgent(llm=MagicMock(), search_client=mock_search_client)
        mock_internal = MagicMock()
        mock_internal.invoke.return_value = _make_agent_response("not an array")
        agent._agent = mock_internal

        result = agent.search_jobs(sample_resume_data)
        assert isinstance(result, list)

    def test_agent_invoked_on_search(self, sample_resume_data, mock_search_client):
        """Internal LangGraph agent should be invoked at least once."""
        agent = JobSearchAgent(llm=MagicMock(), search_client=mock_search_client)
        mock_internal = MagicMock()
        mock_internal.invoke.return_value = _make_agent_response([])
        agent._agent = mock_internal

        agent.search_jobs(sample_resume_data)

        assert mock_internal.invoke.call_count >= 1

    def test_match_scores_within_bounds(self, sample_resume_data, mock_search_client):
        payload = [
            {**_JOB_LIST_PAYLOAD[0], "match_score": 1.5},
            {**_JOB_LIST_PAYLOAD[1], "match_score": -0.2},
        ]
        agent = JobSearchAgent(llm=MagicMock(), search_client=mock_search_client)
        mock_internal = MagicMock()
        mock_internal.invoke.return_value = _make_agent_response(payload)
        agent._agent = mock_internal

        result = agent.search_jobs(sample_resume_data)

        for job in result:
            assert 0.0 <= job.match_score <= 1.0
