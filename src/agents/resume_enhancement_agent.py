"""ResumeEnhancementAgent – tailor a resume to a specific job role using AI.

Each agent is implemented as a LangGraph ReAct agent (create_react_agent) that
calls LangChain @tool-decorated functions to complete its work.
"""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from rich.console import Console

from src.models import EnhancedResume, JobRole, ResumeData
from src.tools.llm_client import get_llm

console = Console()


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool
def extract_job_keywords(job_description: str) -> str:
    """Extract key technical skills, requirements, and action keywords from a job description.

    Args:
        job_description: Full text of the job description.

    Returns:
        Comma-separated list of up to 30 important keywords and skill terms.
    """
    # Tokenise and deduplicate while preserving order
    words = re.findall(r"\b[A-Za-z][a-zA-Z0-9#+/._-]*\b", job_description)
    seen: dict[str, None] = {}
    for w in words:
        seen[w] = None
    return ", ".join(list(seen.keys())[:30])


@tool
def format_resume_section(section_title: str, bullet_points: str) -> str:
    """Format a resume section with a title and bullet points.

    Args:
        section_title: Section heading (e.g. "EXPERIENCE", "SKILLS").
        bullet_points: Newline-separated bullet point strings.

    Returns:
        Formatted resume section text ready for inclusion in a document.
    """
    lines = [f"\n{section_title.upper()}", "=" * len(section_title)]
    for point in bullet_points.split("\n"):
        stripped = point.strip()
        if stripped:
            prefix = "• " if not stripped.startswith(("•", "-", "*")) else ""
            lines.append(f"{prefix}{stripped}")
    return "\n".join(lines)


# All tools exposed by this agent
ENHANCEMENT_TOOLS = [extract_job_keywords, format_resume_section]


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_ENHANCE_SYSTEM_PROMPT = """\
You are an expert resume writer and career coach with access to tools.

Your task:
1. Use `extract_job_keywords` on the job description to identify key terms.
2. Optionally use `format_resume_section` to structure any rewritten sections.
3. Rewrite the candidate's resume to maximise its relevance for the target role:
   - Mirror the job description's keywords and terminology
   - Reorder bullets to highlight the most relevant achievements first
   - Emphasise skills that directly match the role's requirements
   - Keep original facts – do NOT invent experience or credentials
   - Use strong action verbs and quantify achievements where possible
4. Return ONLY a valid JSON object:
{
  "enhanced_text": "Full enhanced resume text here...",
  "changes_summary": "Bullet-point summary of major changes made"
}
"""


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------

def create_enhancement_agent(llm: Any) -> Any:
    """Return a compiled LangGraph ReAct agent for resume enhancement."""
    return create_react_agent(llm, tools=ENHANCEMENT_TOOLS)


# ---------------------------------------------------------------------------
# Public class
# ---------------------------------------------------------------------------

class ResumeEnhancementAgent:
    """Tailor a resume for a specific job role via a LangGraph ReAct agent."""

    def __init__(self, llm: Any = None) -> None:
        self._llm = llm
        self._agent: Any = None  # lazy-init

    def _get_agent(self) -> Any:
        if self._agent is None:
            llm = self._llm if self._llm is not None else get_llm(temperature=0.3)
            self._agent = create_enhancement_agent(llm)
        return self._agent

    def enhance_resume(
        self, resume_data: ResumeData, job_role: JobRole
    ) -> EnhancedResume:
        """Return an :class:`EnhancedResume` tailored for *job_role*."""
        console.print(
            f"[cyan]✍️  Enhancing resume for:[/cyan] {job_role.title} @ {job_role.company}"
        )

        prompt = (
            f"Job Title: {job_role.title}\n"
            f"Company: {job_role.company}\n"
            f"Job Description:\n{job_role.description}\n\n"
            f"Original Resume:\n---\n{resume_data.parsed_text}\n---"
        )

        agent = self._get_agent()
        result = agent.invoke(
            {
                "messages": [
                    SystemMessage(content=_ENHANCE_SYSTEM_PROMPT),
                    HumanMessage(content=prompt),
                ]
            }
        )

        last_msg = result["messages"][-1]
        last_content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
        if not isinstance(last_content, str):
            last_content = " ".join(
                c.get("text", "") if isinstance(c, dict) else str(c)
                for c in last_content
            )

        data = _parse_json_object(str(last_content))
        enhanced_text = data.get("enhanced_text") or resume_data.parsed_text
        changes_summary = data.get("changes_summary", "No changes summary available.")

        return EnhancedResume(
            original_text=resume_data.parsed_text,
            enhanced_text=enhanced_text,
            job_role=job_role,
            changes_summary=changes_summary,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_json_object(text: str) -> dict[str, Any]:
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

    match = re.search(r"\{[\s\S]+\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return {}
