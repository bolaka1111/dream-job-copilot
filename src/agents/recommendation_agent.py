"""RecommendationAgent – rank and explain best-fit roles for the candidate.

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

from src.config import get_settings
from src.models import JobRole, ResumeData
from src.tools.llm_client import get_llm

console = Console()


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool
def compute_skill_overlap(candidate_skills_json: str, job_description: str) -> str:
    """Compute how many candidate skills appear in a job description.

    Args:
        candidate_skills_json: JSON array of candidate skill strings.
        job_description: Full job description text.

    Returns:
        JSON object with overlap_count, overlap_ratio, and matching_skills list.
    """
    try:
        skills: list[str] = json.loads(candidate_skills_json)
    except (json.JSONDecodeError, TypeError):
        skills = []
    desc_lower = job_description.lower()
    matching = [s for s in skills if s.lower() in desc_lower]
    return json.dumps(
        {
            "overlap_count": len(matching),
            "overlap_ratio": round(len(matching) / max(len(skills), 1), 3),
            "matching_skills": matching,
        }
    )


@tool
def format_candidate_profile(resume_data_json: str) -> str:
    """Format a concise candidate profile summary from resume data JSON.

    Args:
        resume_data_json: JSON object with keys: current_role, experience_years,
            skills (list), education (list), target_roles (list), review.

    Returns:
        Human-readable profile summary string.
    """
    try:
        data: dict[str, Any] = json.loads(resume_data_json)
    except (json.JSONDecodeError, TypeError):
        data = {}
    return (
        f"Current role: {data.get('current_role', 'N/A')}\n"
        f"Experience: {data.get('experience_years', 0)} years\n"
        f"Skills: {', '.join(data.get('skills', [])[:15])}\n"
        f"Education: {', '.join(data.get('education', [])[:3])}\n"
        f"Target roles: {', '.join(data.get('target_roles', []))}"
    )


# All tools exposed by this agent
RECOMMENDATION_TOOLS = [compute_skill_overlap, format_candidate_profile]


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_RECOMMEND_SYSTEM_PROMPT = """\
You are an expert career advisor with access to tools.

Your task:
1. Use `format_candidate_profile` to produce a readable summary of the candidate.
2. Optionally use `compute_skill_overlap` on individual jobs to measure fit.
3. Select the TOP N best-fit roles from the provided list, add a "reasoning" field
   explaining why each is a match, and update match_score values.
4. Return ONLY a JSON array of the top roles (keep all original fields), sorted
   by match_score descending. No extra text.

[
  {
    "title": "...", "company": "...", "location": "...", "url": "...",
    "description": "...", "match_score": 0.92, "source": "...",
    "reasoning": "This role aligns because ..."
  },
  ...
]
"""


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------

def create_recommendation_agent(llm: Any) -> Any:
    """Return a compiled LangGraph ReAct agent for job recommendations."""
    return create_react_agent(llm, tools=RECOMMENDATION_TOOLS)


# ---------------------------------------------------------------------------
# Public class
# ---------------------------------------------------------------------------

class RecommendationAgent:
    """Use a LangGraph ReAct agent to rank and explain job role recommendations."""

    def __init__(self, llm: Any = None) -> None:
        self._llm = llm
        self._agent: Any = None  # lazy-init

    def _get_agent(self) -> Any:
        if self._agent is None:
            llm = self._llm if self._llm is not None else get_llm(temperature=0.2)
            self._agent = create_recommendation_agent(llm)
        return self._agent

    def recommend_roles(
        self,
        resume_data: ResumeData,
        jobs: list[JobRole],
        top_n: int | None = None,
    ) -> list[JobRole]:
        """Return the top *top_n* recommended roles sorted by match score.

        Falls back gracefully when *jobs* is empty or the agent returns nothing.
        """
        settings = get_settings()
        n = top_n or settings.max_shortlisted_jobs

        if not jobs:
            console.print("[yellow]⚠️  No jobs to recommend from.[/yellow]")
            return []

        console.print(f"[cyan]🤖 Recommending top {n} roles from {len(jobs)} candidates…[/cyan]")

        resume_json = resume_data.model_dump_json()
        jobs_json = json.dumps([j.model_dump() for j in jobs[:40]], indent=2)

        prompt = (
            f"Candidate resume data (JSON):\n{resume_json}\n\n"
            f"Available jobs (JSON array, {len(jobs)} total):\n{jobs_json}\n\n"
            f"Please recommend the TOP {n} best-fit roles."
        )

        agent = self._get_agent()
        result = agent.invoke(
            {
                "messages": [
                    SystemMessage(
                        content=_RECOMMEND_SYSTEM_PROMPT.replace("TOP N", f"TOP {n}")
                    ),
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
        data = _parse_json_array(str(last_content))

        recommended: list[JobRole] = []
        for item in data:
            try:
                recommended.append(JobRole(**item))
            except Exception:
                continue

        # Fallback: return top-N by existing match_score if agent returned nothing
        if not recommended:
            console.print("[yellow]⚠️  Agent returned no recommendations; using score fallback.[/yellow]")
            recommended = sorted(jobs, key=lambda j: j.match_score, reverse=True)

        result_list = recommended[:n]
        console.print(f"[green]✅ {len(result_list)} roles recommended.[/green]")
        return result_list


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
