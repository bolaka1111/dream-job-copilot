"""Tests for ResumeAgent – parsing and AI-review logic."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.agents.resume_agent import ResumeAgent, _parse_json_response
from src.models import ResumeData


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_llm_response(payload: dict) -> MagicMock:
    """Create a mock LLM response with the given JSON payload."""
    response = MagicMock()
    response.content = json.dumps(payload)
    return response


_VALID_PAYLOAD = {
    "skills": ["Python", "FastAPI", "Docker"],
    "experience_years": 5.0,
    "education": ["B.Sc. CS – MIT (2019)"],
    "current_role": "Software Engineer",
    "target_roles": ["Senior Engineer", "Staff Engineer"],
    "review": "Strong backend profile.",
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
# Tests for ResumeAgent
# ---------------------------------------------------------------------------

class TestResumeAgent:
    def test_parse_and_review_pdf(self, tmp_path, mock_llm):
        """parse_and_review should call parse_pdf and return ResumeData."""
        resume_file = tmp_path / "resume.pdf"
        resume_file.write_bytes(b"%PDF fake content")

        mock_llm.invoke.return_value = _make_llm_response(_VALID_PAYLOAD)

        with patch("src.agents.resume_agent.parse_resume", return_value="Jane Doe resume text"):
            agent = ResumeAgent(llm=mock_llm)
            result = agent.parse_and_review(str(resume_file))

        assert isinstance(result, ResumeData)
        assert result.current_role == "Software Engineer"
        assert "Python" in result.skills
        assert result.experience_years == 5.0
        assert result.parsed_text == "Jane Doe resume text"

    def test_parse_and_review_docx(self, tmp_path, mock_llm):
        """parse_and_review should work with DOCX files too."""
        resume_file = tmp_path / "resume.docx"
        resume_file.write_bytes(b"PK fake docx")

        mock_llm.invoke.return_value = _make_llm_response(_VALID_PAYLOAD)

        with patch("src.agents.resume_agent.parse_resume", return_value="John Smith resume"):
            agent = ResumeAgent(llm=mock_llm)
            result = agent.parse_and_review(str(resume_file))

        assert result.parsed_text == "John Smith resume"
        assert result.education == ["B.Sc. CS – MIT (2019)"]

    def test_empty_file_raises(self, tmp_path, mock_llm):
        """An empty parsed text should raise ValueError."""
        with patch("src.agents.resume_agent.parse_resume", return_value="   "):
            agent = ResumeAgent(llm=mock_llm)
            with pytest.raises(ValueError, match="Could not extract"):
                agent.parse_and_review("resume.pdf")

    def test_llm_partial_response_graceful(self, tmp_path, mock_llm):
        """Partial LLM JSON (missing fields) should still produce a ResumeData."""
        partial_payload = {"skills": ["Python"], "current_role": "Engineer"}
        mock_llm.invoke.return_value = _make_llm_response(partial_payload)

        with patch("src.agents.resume_agent.parse_resume", return_value="Some resume"):
            agent = ResumeAgent(llm=mock_llm)
            result = agent.parse_and_review("resume.pdf")

        assert result.skills == ["Python"]
        assert result.experience_years == 0.0  # default
        assert result.target_roles == []  # default

    def test_llm_called_once(self, mock_llm):
        """LLM should be invoked exactly once per call."""
        mock_llm.invoke.return_value = _make_llm_response(_VALID_PAYLOAD)

        with patch("src.agents.resume_agent.parse_resume", return_value="resume text"):
            agent = ResumeAgent(llm=mock_llm)
            agent.parse_and_review("resume.pdf")

        assert mock_llm.invoke.call_count == 1

    def test_review_field_populated(self, mock_llm):
        """The review field from the LLM should appear in ResumeData."""
        payload = {**_VALID_PAYLOAD, "review": "Excellent candidate."}
        mock_llm.invoke.return_value = _make_llm_response(payload)

        with patch("src.agents.resume_agent.parse_resume", return_value="text"):
            agent = ResumeAgent(llm=mock_llm)
            result = agent.parse_and_review("resume.pdf")

        assert result.review == "Excellent candidate."
