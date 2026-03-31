"""RecommendationAgent – rank and explain best-fit roles for the candidate."""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from rich.console import Console

from src.config import get_settings
from src.models import JobRole, ResumeData
from src.tools.llm_client import get_llm

console = Console()

_RECOMMEND_SYSTEM_PROMPT = """\
You are an expert career advisor. Given a candidate's profile and a list of job roles,
identify the TOP N best-fit roles and explain why each is a great match.

Return ONLY a JSON array of the top roles (keep all original fields, update match_score
and add a "reasoning" field):
[
  {
    "title": "...",
    "company": "...",
    "location": "...",
    "url": "...",
    "description": "...",
    "match_score": 0.92,
    "source": "...",
    "reasoning": "This role aligns because ..."
  },
  ...
]

Sort by match_score descending. Be rigorous: only include roles where there is genuine fit.
"""


class RecommendationAgent:
    """Use an LLM to rank and explain job role recommendations."""

    def __init__(self, llm: Any = None) -> None:
        self._llm = llm

    def _get_llm(self) -> Any:
        return self._llm if self._llm is not None else get_llm(temperature=0.2)

    def recommend_roles(
        self,
        resume_data: ResumeData,
        jobs: list[JobRole],
        top_n: int | None = None,
    ) -> list[JobRole]:
        """Return the top *top_n* recommended roles sorted by match score.

        Falls back gracefully when *jobs* is empty or LLM returns nothing.
        """
        settings = get_settings()
        n = top_n or settings.max_shortlisted_jobs

        if not jobs:
            console.print("[yellow]⚠️  No jobs to recommend from.[/yellow]")
            return []

        console.print(f"[cyan]🤖 Recommending top {n} roles from {len(jobs)} candidates…[/cyan]")

        candidate_summary = _candidate_summary(resume_data)
        jobs_json = json.dumps([j.model_dump() for j in jobs[:40]], indent=2)

        llm = self._get_llm()
        messages = [
            SystemMessage(content=_RECOMMEND_SYSTEM_PROMPT.replace("TOP N", f"TOP {n}")),
            HumanMessage(
                content=(
                    f"Candidate:\n{candidate_summary}\n\n"
                    f"Available jobs (JSON):\n{jobs_json}"
                )
            ),
        ]
        response = llm.invoke(messages)
        content = response.content if hasattr(response, "content") else str(response)
        data = _parse_json_array(content)

        recommended: list[JobRole] = []
        for item in data:
            try:
                recommended.append(JobRole(**item))
            except Exception:
                continue

        # Fallback: return top-N by existing match_score if LLM returned nothing
        if not recommended:
            console.print("[yellow]⚠️  LLM returned no recommendations; using score fallback.[/yellow]")
            recommended = sorted(jobs, key=lambda j: j.match_score, reverse=True)

        result = recommended[:n]
        console.print(f"[green]✅ {len(result)} roles recommended.[/green]")
        return result


def _candidate_summary(resume_data: ResumeData) -> str:
    return (
        f"Current role: {resume_data.current_role}\n"
        f"Experience: {resume_data.experience_years} years\n"
        f"Key skills: {', '.join(resume_data.skills[:15])}\n"
        f"Education: {', '.join(resume_data.education[:3])}\n"
        f"Target roles: {', '.join(resume_data.target_roles)}\n"
        f"Resume review excerpt:\n{resume_data.review[:400]}"
    )


def _parse_json_array(text: str) -> list[dict[str, Any]]:
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if match:
        try:
            result = json.loads(match.group(1))
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    match = re.search(r"\[[\s\S]+\]", text)
    if match:
        try:
            result = json.loads(match.group(0))
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    return []
