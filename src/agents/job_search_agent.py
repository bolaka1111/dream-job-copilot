"""JobSearchAgent – search the job market based on resume data.

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
from src.tools.search_client import SearchClient

console = Console()


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SCORE_SYSTEM_PROMPT = """\
You are a senior recruiter with access to job search tools.

Your task:
1. Use the `search_jobs_online` tool to search for job postings using the provided queries.
   Call the tool once per query.
2. Collect all results, remove duplicates, and score each job's relevance to the
   candidate profile (0.0 to 1.0).
3. Return ONLY a JSON array of scored job objects:
[
  {
    "title": "Job Title",
    "company": "Company Name",
    "location": "City, Country or Remote",
    "url": "https://...",
    "description": "1-2 sentence summary",
    "match_score": 0.85,
    "source": "tavily"
  },
  ...
]

Score guidelines:
- 0.8-1.0: Excellent fit (skills, experience, seniority all match)
- 0.6-0.8: Good fit (most criteria match)
- 0.4-0.6: Partial fit (some transferable skills)
- below 0.4: Poor fit
"""


# ---------------------------------------------------------------------------
# Tool factory
# ---------------------------------------------------------------------------

def make_search_jobs_tool(search_client: SearchClient, max_results_per_query: int = 10) -> Any:
    """Return a LangChain tool that searches for jobs via *search_client*."""

    @tool
    def search_jobs_online(query: str) -> str:
        """Search for job postings online matching the given query.

        Args:
            query: Search query string, e.g. "Staff Engineer Python remote".

        Returns:
            JSON array of raw job search results from the web.
        """
        results = search_client.search_jobs(query, max_results=max_results_per_query)
        return json.dumps(results)

    return search_jobs_online


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------

def create_job_search_agent(
    llm: Any,
    search_client: SearchClient,
    max_results: int = 10,
) -> Any:
    """Return a compiled LangGraph ReAct agent for job market search."""
    search_tool = make_search_jobs_tool(search_client, max_results_per_query=max_results)
    return create_react_agent(llm, tools=[search_tool])


# ---------------------------------------------------------------------------
# Public class
# ---------------------------------------------------------------------------

class JobSearchAgent:
    """Search job market and rank results against a candidate's profile."""

    def __init__(
        self,
        llm: Any = None,
        search_client: SearchClient | None = None,
    ) -> None:
        self._llm = llm
        self._search_client = search_client
        self._agent: Any = None  # lazy-init

    def _get_agent(self) -> Any:
        if self._agent is None:
            llm = self._llm if self._llm is not None else get_llm(temperature=0.1)
            client = self._search_client if self._search_client is not None else SearchClient()
            settings = get_settings()
            self._agent = create_job_search_agent(llm, client, settings.max_job_results)
        return self._agent

    def search_jobs(self, resume_data: ResumeData) -> list[JobRole]:
        """Build queries from *resume_data*, search, score and return JobRole list."""
        queries = _build_queries(resume_data)
        candidate_summary = _candidate_summary(resume_data)

        console.print(f"[cyan]🔍 Searching for jobs with {len(queries)} queries…[/cyan]")

        prompt = (
            f"Search for job openings matching this candidate profile:\n{candidate_summary}\n\n"
            f"Use the search_jobs_online tool for each of the following queries:\n"
            + "\n".join(f"- {q}" for q in queries)
            + "\n\nAfter all searches, score each result and return ONLY a JSON array."
        )

        agent = self._get_agent()
        result = agent.invoke(
            {
                "messages": [
                    SystemMessage(content=_SCORE_SYSTEM_PROMPT),
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

        jobs: list[JobRole] = []
        for item in data:
            try:
                jobs.append(JobRole(**item))
            except Exception:
                continue

        jobs.sort(key=lambda j: j.match_score, reverse=True)

        if not jobs:
            console.print("[yellow]⚠️  No job results found.[/yellow]")
        else:
            console.print(f"[green]✅ Found {len(jobs)} relevant job postings.[/green]")

        return jobs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_queries(resume_data: ResumeData) -> list[str]:
    """Build 2-3 targeted search queries from the resume."""
    queries: list[str] = []

    # Primary: target roles + top skills
    top_skills = " ".join(resume_data.skills[:5])
    for role in resume_data.target_roles[:2]:
        queries.append(f"{role} job opening {top_skills}")

    # Fallback: current role if no target roles
    if not queries and resume_data.current_role:
        queries.append(f"{resume_data.current_role} job opening")

    if not queries:
        queries.append("software engineer job opening 2024")

    return queries


def _candidate_summary(resume_data: ResumeData) -> str:
    return (
        f"Role: {resume_data.current_role}\n"
        f"Experience: {resume_data.experience_years} years\n"
        f"Skills: {', '.join(resume_data.skills[:20])}\n"
        f"Target roles: {', '.join(resume_data.target_roles)}"
    )


def _parse_json_array(text: str) -> list[dict[str, Any]]:
    """Extract the first JSON array from LLM output."""
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
