"""ResumeEnhancementAgent – tailor a resume to a specific job role using AI."""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from rich.console import Console

from src.models import EnhancedResume, JobRole, ResumeData
from src.tools.llm_client import get_llm

console = Console()

_ENHANCE_SYSTEM_PROMPT = """\
You are an expert resume writer and career coach.
Given a candidate's original resume text and a specific job description,
rewrite the resume to maximise its relevance for that role.

Guidelines:
- Mirror the job description's keywords and terminology
- Reorder experience bullets to highlight the most relevant achievements first
- Emphasise skills that directly match the role's requirements
- Keep the original facts — do NOT invent experience or credentials
- Use strong action verbs and quantify achievements where possible
- Keep the length similar to the original (do not drastically pad or cut)

Return ONLY a valid JSON object:
{
  "enhanced_text": "Full enhanced resume text here...",
  "changes_summary": "Bullet-point summary of major changes made"
}
"""


class ResumeEnhancementAgent:
    """Tailor a resume for a specific job role using an LLM."""

    def __init__(self, llm: Any = None) -> None:
        self._llm = llm

    def _get_llm(self) -> Any:
        return self._llm if self._llm is not None else get_llm(temperature=0.3)

    def enhance_resume(
        self, resume_data: ResumeData, job_role: JobRole
    ) -> EnhancedResume:
        """Return an :class:`EnhancedResume` tailored for *job_role*."""
        console.print(
            f"[cyan]✍️  Enhancing resume for:[/cyan] {job_role.title} @ {job_role.company}"
        )

        llm = self._get_llm()
        messages = [
            SystemMessage(content=_ENHANCE_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Job Title: {job_role.title}\n"
                    f"Company: {job_role.company}\n"
                    f"Job Description:\n{job_role.description}\n\n"
                    f"Original Resume:\n---\n{resume_data.parsed_text}\n---"
                )
            ),
        ]
        response = llm.invoke(messages)
        content = response.content if hasattr(response, "content") else str(response)
        data = _parse_json_object(content)

        enhanced_text = data.get("enhanced_text") or resume_data.parsed_text
        changes_summary = data.get("changes_summary", "No changes summary available.")

        return EnhancedResume(
            original_text=resume_data.parsed_text,
            enhanced_text=enhanced_text,
            job_role=job_role,
            changes_summary=changes_summary,
        )


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
