"""ResumeAgent – parse a resume file and produce an AI-reviewed ResumeData."""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from rich.console import Console

from src.models import ResumeData
from src.tools.llm_client import get_llm
from src.tools.resume_parser import parse_resume

console = Console()

_SYSTEM_PROMPT = """\
You are an expert career coach and resume analyst.
Given the raw text of a resume, extract structured information and write a concise review.

Return ONLY a valid JSON object with these keys:
{
  "skills": ["list", "of", "skills"],
  "experience_years": <float>,
  "education": ["Degree – Institution – Year", ...],
  "current_role": "Most recent job title",
  "target_roles": ["role 1", "role 2", ...],
  "review": "2-3 paragraph AI review of the resume strengths, gaps, and suggestions"
}

Rules:
- skills: include both technical (languages, tools, frameworks) and soft skills
- experience_years: total professional experience in years (decimal ok)
- education: one entry per degree/certification
- target_roles: infer 2-5 likely desired roles from the candidate's background
- review: be constructive, specific, and actionable
"""


class ResumeAgent:
    """Parse a resume file and analyse it with an LLM."""

    def __init__(self, llm: Any = None) -> None:
        self._llm = llm  # allow injection for testing

    def _get_llm(self) -> Any:
        if self._llm is not None:
            return self._llm
        return get_llm(temperature=0.1)

    def parse_and_review(self, resume_path: str) -> ResumeData:
        """Parse *resume_path* and return enriched ResumeData.

        Steps:
        1. Extract raw text via PyPDF2 / python-docx.
        2. Ask the LLM to extract structured fields and write a review.
        3. Return a validated ResumeData instance.
        """
        console.print(f"[cyan]📄 Parsing resume:[/cyan] {resume_path}")

        raw_text = parse_resume(resume_path)
        if not raw_text.strip():
            raise ValueError(f"Could not extract any text from '{resume_path}'.")

        console.print("[cyan]🤖 Analysing resume with AI…[/cyan]")
        extracted = self._extract_with_llm(raw_text)

        resume_data = ResumeData(
            parsed_text=raw_text,
            skills=extracted.get("skills", []),
            experience_years=extracted.get("experience_years", 0.0),
            education=extracted.get("education", []),
            current_role=extracted.get("current_role", ""),
            target_roles=extracted.get("target_roles", []),
            review=extracted.get("review", ""),
        )
        console.print("[green]✅ Resume analysis complete.[/green]")
        return resume_data

    def _extract_with_llm(self, raw_text: str) -> dict[str, Any]:
        """Send raw text to the LLM and parse the JSON response."""
        llm = self._get_llm()
        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(
                content=f"Please analyse this resume:\n\n---\n{raw_text}\n---"
            ),
        ]
        response = llm.invoke(messages)
        content = response.content if hasattr(response, "content") else str(response)
        return _parse_json_response(content)


def _parse_json_response(text: str) -> dict[str, Any]:
    """Extract the first JSON object from an LLM text response."""
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown code fences
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Find first { ... } block
    brace_match = re.search(r"\{[\s\S]+\}", text)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    return {}
