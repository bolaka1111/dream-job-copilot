"""ReviewAgent – fetch and parse employee reviews for shortlisted companies.

Each agent is implemented as a LangGraph ReAct agent (create_react_agent) that
calls LangChain @tool-decorated functions to complete its work.
"""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain.agents import create_agent as create_react_agent
from rich.console import Console

from src.models import EmployeeReview, JobRole
from src.tools.llm_client import get_llm
from src.tools.search_client import SearchClient

console = Console()


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_REVIEW_SYSTEM_PROMPT = """\
You are an HR analyst with access to a web search tool.

Your task:
1. Use the `search_employee_reviews` tool to find employee review data for the
   given company.
2. Analyse the returned snippets and extract key insights.
3. Return ONLY a valid JSON object:
{
  "company": "Company Name",
  "rating": <float 0-5>,
  "pros": ["pro 1", "pro 2", ...],
  "cons": ["con 1", "con 2", ...],
  "review_count": <int>,
  "summary": "2-3 sentence summary of the employee experience"
}

If rating cannot be determined, use 0.0. Base review_count on any numbers mentioned.
"""


# ---------------------------------------------------------------------------
# Tool factory
# ---------------------------------------------------------------------------

def make_search_employee_reviews_tool(search_client: SearchClient) -> Any:
    """Return a LangChain tool that searches for employee reviews via *search_client*."""

    @tool
    def search_employee_reviews(company_name: str) -> str:
        """Search for employee reviews of a company from sites like Glassdoor and Indeed.

        Args:
            company_name: Name of the company to search reviews for.

        Returns:
            JSON array of raw review snippets from the web.
        """
        results = search_client.search_company_reviews(company_name)
        return json.dumps(results)

    return search_employee_reviews


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------

def create_review_agent(llm: Any, search_client: SearchClient) -> Any:
    """Return a compiled LangGraph ReAct agent for fetching employee reviews."""
    review_tool = make_search_employee_reviews_tool(search_client)
    return create_react_agent(llm, tools=[review_tool])


# ---------------------------------------------------------------------------
# Public class
# ---------------------------------------------------------------------------

class ReviewAgent:
    """Fetch employee reviews for shortlisted job companies via a LangGraph ReAct agent."""

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
            self._agent = create_review_agent(llm, client)
        return self._agent

    def fetch_reviews(
        self, jobs: list[JobRole]
    ) -> list[tuple[JobRole, EmployeeReview]]:
        """Return each job paired with an :class:`EmployeeReview`.

        Deduplicates companies so each is searched only once.
        """
        if not jobs:
            return []

        agent = self._get_agent()

        # Cache reviews per company to avoid duplicate agent invocations
        review_cache: dict[str, EmployeeReview] = {}
        results: list[tuple[JobRole, EmployeeReview]] = []

        for job in jobs:
            company = job.company
            if company not in review_cache:
                console.print(f"[cyan]🔍 Fetching reviews for:[/cyan] {company}")
                review = self._fetch_review_for_company(company, agent)
                review_cache[company] = review

            results.append((job, review_cache[company]))

        console.print(f"[green]✅ Reviews fetched for {len(review_cache)} companies.[/green]")
        return results

    def _fetch_review_for_company(self, company: str, agent: Any) -> EmployeeReview:
        """Run the LangGraph agent to fetch and parse reviews for one company."""
        result = agent.invoke(
            {
                "messages": [
                    SystemMessage(content=_REVIEW_SYSTEM_PROMPT),
                    HumanMessage(
                        content=(
                            f"Please fetch and analyse employee reviews for: {company}"
                        )
                    ),
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
        if not data:
            return EmployeeReview(company=company, summary="Could not parse review data.")

        data.setdefault("company", company)
        try:
            return EmployeeReview(**data)
        except Exception:
            return EmployeeReview(company=company, summary=str(data.get("summary", "")))


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

    match = re.search(r"\{[\s\S]+\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return {}
