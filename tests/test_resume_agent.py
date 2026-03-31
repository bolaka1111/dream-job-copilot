"""Tests for ResumeAgent – parsing and AI-review logic."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from langchain_core.messages import AIMessage, ToolMessage

from src.agents.resume_agent import (
    RESUME_TOOLS,
    ResumeAgent,
    _parse_json_response,
    create_resume_agent,
    parse_resume_file,
)
from src.models import ResumeData


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_PAYLOAD = {
    "skills": ["Python", "FastAPI", "Docker"],
    "experience_years": 5.0,
    "education": ["B.Sc. CS – MIT (2019)"],
    "current_role": "Software Engineer",
    "target_roles": ["Senior Engineer", "Staff Engineer"],
    "review": "Strong backend profile.",
}


def _make_agent_response(raw_text: str, payload: dict) -> dict:
    """Build a mock LangGraph agent result dict with tool + final messages."""
    return {
        "messages": [
            ToolMessage(
                content=raw_text,
                name="parse_resume_file",
                tool_call_id="call_1",
            ),
            AIMessage(content=json.dumps(payload)),
        ]
    }


# ---------------------------------------------------------------------------
# Tests for _parse_json_response helper
# ---------------------------------------------------------------------------

class TestParseJsonResponse:
    def test_plain_json(self):
        result = _parse_json_response(json.dumps({"key": "value"}))
        assert result == {"key": "value"}

    def test_markdown_fenced_json(self):
        text = '```json\n{"key": "value"}\n```'
        result = _parse_json_response(text)
        assert result == {"key": "value"}

    def test_json_embedded_in_prose(self):
        text = 'Here is the result: {"key": "value"} as requested.'
        result = _parse_json_response(text)
        assert result == {"key": "value"}

    def test_invalid_returns_empty(self):
        result = _parse_json_response("not json at all")
        assert result == {}


# ---------------------------------------------------------------------------
# Tests for the parse_resume_file tool
# ---------------------------------------------------------------------------

class TestParseResumeFileTool:
    def test_tool_is_in_resume_tools(self):
        assert parse_resume_file in RESUME_TOOLS

    def test_tool_calls_parser(self, tmp_path):
        """parse_resume_file tool should delegate to the resume parser."""
        with patch("src.agents.resume_agent._parse_resume", return_value="Jane Doe text") as mock_parser:
            result = parse_resume_file.invoke({"file_path": "resume.pdf"})
        mock_parser.assert_called_once_with("resume.pdf")
        assert result == "Jane Doe text"

    def test_create_resume_agent_returns_graph(self):
        """create_resume_agent should return a runnable LangGraph object."""
        mock_llm = MagicMock()
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)
        # Just verify the factory returns without error and has an invoke method
        agent = create_resume_agent(mock_llm)
        assert hasattr(agent, "invoke")


# ---------------------------------------------------------------------------
# Tests for ResumeAgent
# ---------------------------------------------------------------------------

class TestResumeAgent:
    def test_parse_and_review_pdf(self, tmp_path):
        """parse_and_review should return ResumeData with data from the agent."""
        resume_file = tmp_path / "resume.pdf"
        resume_file.write_bytes(b"%PDF fake content")

        agent = ResumeAgent(llm=MagicMock())

        mock_internal = MagicMock()
        mock_internal.invoke.return_value = _make_agent_response(
            "Jane Doe resume text", _VALID_PAYLOAD
        )
        agent._agent = mock_internal

        result = agent.parse_and_review(str(resume_file))

        assert isinstance(result, ResumeData)
        assert result.current_role == "Software Engineer"
        assert "Python" in result.skills
        assert result.experience_years == 5.0
        assert result.parsed_text == "Jane Doe resume text"

    def test_parse_and_review_docx(self, tmp_path):
        """parse_and_review should work with DOCX files too."""
        resume_file = tmp_path / "resume.docx"
        resume_file.write_bytes(b"PK fake docx")

        agent = ResumeAgent(llm=MagicMock())

        mock_internal = MagicMock()
        mock_internal.invoke.return_value = _make_agent_response(
            "John Smith resume", _VALID_PAYLOAD
        )
        agent._agent = mock_internal

        result = agent.parse_and_review(str(resume_file))

        assert result.parsed_text == "John Smith resume"
        assert result.education == ["B.Sc. CS – MIT (2019)"]

    def test_empty_file_raises(self, tmp_path):
        """An empty raw text in the ToolMessage should raise ValueError."""
        agent = ResumeAgent(llm=MagicMock())

        mock_internal = MagicMock()
        mock_internal.invoke.return_value = _make_agent_response(
            "   ", _VALID_PAYLOAD
        )
        agent._agent = mock_internal

        with pytest.raises(ValueError, match="Could not extract"):
            agent.parse_and_review("resume.pdf")

    def test_llm_partial_response_graceful(self, tmp_path):
        """Partial agent JSON (missing fields) should still produce a ResumeData."""
        partial_payload = {"skills": ["Python"], "current_role": "Engineer"}

        agent = ResumeAgent(llm=MagicMock())
        mock_internal = MagicMock()
        mock_internal.invoke.return_value = _make_agent_response(
            "Some resume", partial_payload
        )
        agent._agent = mock_internal

        result = agent.parse_and_review("resume.pdf")

        assert result.skills == ["Python"]
        assert result.experience_years == 0.0  # default
        assert result.target_roles == []  # default

    def test_agent_invoked_once(self):
        """The internal LangGraph agent should be invoked exactly once per call."""
        agent = ResumeAgent(llm=MagicMock())
        mock_internal = MagicMock()
        mock_internal.invoke.return_value = _make_agent_response(
            "resume text", _VALID_PAYLOAD
        )
        agent._agent = mock_internal

        agent.parse_and_review("resume.pdf")

        assert mock_internal.invoke.call_count == 1

    def test_review_field_populated(self):
        """The review field from the agent should appear in ResumeData."""
        payload = {**_VALID_PAYLOAD, "review": "Excellent candidate."}

        agent = ResumeAgent(llm=MagicMock())
        mock_internal = MagicMock()
        mock_internal.invoke.return_value = _make_agent_response("text", payload)
        agent._agent = mock_internal

        result = agent.parse_and_review("resume.pdf")

        assert result.review == "Excellent candidate."
