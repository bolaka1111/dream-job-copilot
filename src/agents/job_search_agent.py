"""JobSearchAgent – search the job market based on resume data."""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from rich.console import Console

from src.config import get_settings
from src.models import JobRole, ResumeData
from src.tools.llm_client import get_llm
from src.tools.search_client import SearchClient

console = Console()

_SCORE_SYSTEM_PROMPT = """\
You are a senior recruiter. Given a candidate profile and a list of job search results,
score each job's relevance to the candidate (0.0 to 1.0) and extract structured data.

Return ONLY a JSON array:
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


class JobSearchAgent:
    """Search job market and rank results against a candidate's profile."""

    def __init__(
        self,
        llm: Any = None,
        search_client: SearchClient | None = None,
    ) -> None:
        self._llm = llm
        self._search_client = search_client

    def _get_llm(self) -> Any:
        return self._llm if self._llm is not None else get_llm(temperature=0.1)

    def _get_search_client(self) -> SearchClient:
        if self._search_client is not None:
            return self._search_client
        return SearchClient()

    def search_jobs(self, resume_data: ResumeData) -> list[JobRole]:
        """Build queries from *resume_data*, search, score and return JobRole list."""
        settings = get_settings()
        queries = _build_queries(resume_data)
        raw_results: list[dict[str, Any]] = []

        client = self._get_search_client()
        for query in queries:
            console.print(f"[cyan]🔍 Searching:[/cyan] {query}")
            results = client.search_jobs(query, max_results=settings.max_job_results // len(queries))
            raw_results.extend(results)

        if not raw_results:
            console.print("[yellow]⚠️  No job results found.[/yellow]")
            return []

        console.print(
            f"[cyan]🤖 Scoring {len(raw_results)} results against your profile…[/cyan]"
        )
        scored = self._score_with_llm(resume_data, raw_results)
        scored.sort(key=lambda j: j.match_score, reverse=True)
        console.print(f"[green]✅ Found {len(scored)} relevant job postings.[/green]")
        return scored

    def _score_with_llm(
        self, resume_data: ResumeData, raw: list[dict[str, Any]]
    ) -> list[JobRole]:
        """Ask LLM to score and structure raw search results."""
        candidate_summary = (
            f"Role: {resume_data.current_role}\n"
            f"Experience: {resume_data.experience_years} years\n"
            f"Skills: {', '.join(resume_data.skills[:20])}\n"
            f"Target roles: {', '.join(resume_data.target_roles)}"
        )
        raw_text = json.dumps(raw[:30], indent=2)  # cap at 30 to stay within context

        llm = self._get_llm()
        messages = [
            SystemMessage(content=_SCORE_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Candidate profile:\n{candidate_summary}\n\n"
                    f"Search results (JSON):\n{raw_text}"
                )
            ),
        ]
        response = llm.invoke(messages)
        content = response.content if hasattr(response, "content") else str(response)
        data = _parse_json_array(content)

        jobs: list[JobRole] = []
        for item in data:
            try:
                jobs.append(JobRole(**item))
            except Exception:
                continue
        return jobs


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
