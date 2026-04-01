"""ResumeAgent – parse a resume file and produce an AI-reviewed ResumeData.

Each agent is implemented as a LangGraph ReAct agent (create_react_agent) that
calls LangChain @tool-decorated functions to complete its work.
"""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from rich.console import Console

from src.models import ResumeData
from src.tools.llm_client import get_llm
from src.tools.resume_parser import parse_resume as _parse_resume

console = Console()


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool
def parse_resume_file(file_path: str) -> str:
    """Parse a resume file (PDF or DOCX) and return the full extracted text.

    Args:
        file_path: Absolute or relative path to the resume file (.pdf or .docx).

    Returns:
        The full plain-text content of the resume.
    """
    return _parse_resume(file_path)


# All tools exposed by this agent
RESUME_TOOLS = [parse_resume_file]


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are an expert career coach and resume analyst with access to tools.

Your task:
1. Use the `parse_resume_file` tool to read the resume from the given file path.
2. From the extracted text, identify:
   - skills: list of technical and soft skills
   - experience_years: total professional experience (decimal, e.g. 7.5)
   - education: list of "Degree – Institution – Year" strings
   - current_role: most recent job title
   - target_roles: 2-5 suitable next-step roles inferred from the background
   - review: 2-3 paragraph constructive review (strengths, gaps, suggestions)
3. Respond with ONLY a valid JSON object containing those keys – no extra text.
"""


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------

def create_resume_agent(llm: Any) -> Any:
    """Return a compiled LangGraph ReAct agent for resume parsing and analysis."""
    return create_react_agent(llm, tools=RESUME_TOOLS)


# ---------------------------------------------------------------------------
# Public class
# ---------------------------------------------------------------------------

class ResumeAgent:
    """Parse a resume file and analyse it with a LangGraph ReAct agent."""

    def __init__(self, llm: Any = None) -> None:
        self._llm = llm  # allow injection for testing
        self._agent: Any = None  # lazy-init to avoid API key checks at import time

    def _get_agent(self) -> Any:
        if self._agent is None:
            llm = self._llm if self._llm is not None else get_llm(temperature=0.1)
            self._agent = create_resume_agent(llm)
        return self._agent

    def parse_and_review(self, resume_path: str) -> ResumeData:
        """Parse *resume_path* and return enriched ResumeData.

        The internal LangGraph ReAct agent calls the ``parse_resume_file`` tool
        to read the file, then uses its LLM reasoning to extract structured
        fields and write a constructive review.
        """
        console.print(f"[cyan]📄 Parsing resume:[/cyan] {resume_path}")
        console.print("[cyan]🤖 Analysing resume with AI…[/cyan]")

        agent = self._get_agent()
        result = agent.invoke(
            {
                "messages": [
                    SystemMessage(content=_SYSTEM_PROMPT),
                    HumanMessage(
                        content=f"Please analyse the resume at: {resume_path}"
                    ),
                ]
            }
        )

        # Extract raw text from the ToolMessage produced by parse_resume_file
        raw_text = ""
        for msg in result["messages"]:
            if isinstance(msg, ToolMessage) and getattr(msg, "name", "") == "parse_resume_file":
                raw_text = msg.content
                break

        if not raw_text.strip():
            raise ValueError(f"Could not extract any text from '{resume_path}'.")

        # Extract structured JSON from the final AI message
        last_msg = result["messages"][-1]
        last_content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
        if not isinstance(last_content, str):
            last_content = " ".join(
                c.get("text", "") if isinstance(c, dict) else str(c)
                for c in last_content
            )
        extracted = _parse_json_response(str(last_content))

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_json_response(text: str) -> dict[str, Any]:
    """Extract the first JSON object from an LLM text response."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    brace_match = re.search(r"\{[\s\S]+\}", text)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    return {}
