"""ReviewAgent – fetch and parse employee reviews for shortlisted companies."""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from rich.console import Console

from src.models import EmployeeReview, JobRole
from src.tools.llm_client import get_llm
from src.tools.search_client import SearchClient

console = Console()

_REVIEW_SYSTEM_PROMPT = """\
You are an HR analyst. Given raw web search snippets about employee reviews for a company,
extract and summarise the key insights.

Return ONLY a valid JSON object:
{
  "company": "Company Name",
  "rating": <float 0-5>,
  "pros": ["pro 1", "pro 2", ...],
  "cons": ["con 1", "con 2", ...],
  "review_count": <int>,
  "summary": "2-3 sentence summary of the employee experience"
}

If you cannot determine the rating, use 0.0. Base review_count on any numbers mentioned.
"""


class ReviewAgent:
    """Fetch employee reviews for shortlisted job companies."""

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
        return self._search_client if self._search_client is not None else SearchClient()

    def fetch_reviews(
        self, jobs: list[JobRole]
    ) -> list[tuple[JobRole, EmployeeReview]]:
        """Return each job paired with an :class:`EmployeeReview`.

        Deduplicates companies so each is searched only once.
        """
        if not jobs:
            return []

        client = self._get_search_client()
        llm = self._get_llm()

        # Cache reviews per company to avoid duplicate searches
        review_cache: dict[str, EmployeeReview] = {}
        results: list[tuple[JobRole, EmployeeReview]] = []

        for job in jobs:
            company = job.company
            if company not in review_cache:
                console.print(f"[cyan]🔍 Fetching reviews for:[/cyan] {company}")
                raw = client.search_company_reviews(company)
                review = self._parse_reviews(company, raw, llm)
                review_cache[company] = review

            results.append((job, review_cache[company]))

        console.print(f"[green]✅ Reviews fetched for {len(review_cache)} companies.[/green]")
        return results

    def _parse_reviews(
        self,
        company: str,
        raw_results: list[dict[str, Any]],
        llm: Any,
    ) -> EmployeeReview:
        """Ask LLM to parse raw search snippets into a structured EmployeeReview."""
        if not raw_results:
            return EmployeeReview(company=company, summary="No review data found.")

        snippets = "\n\n".join(
            f"[{r.get('title', '')}]\n{r.get('content', r.get('snippet', ''))}"
            for r in raw_results[:5]
        )
        messages = [
            SystemMessage(content=_REVIEW_SYSTEM_PROMPT),
            HumanMessage(
                content=f"Company: {company}\n\nReview snippets:\n{snippets}"
            ),
        ]
        response = llm.invoke(messages)
        content = response.content if hasattr(response, "content") else str(response)
        data = _parse_json_object(content)

        if not data:
            return EmployeeReview(company=company, summary="Could not parse review data.")

        data.setdefault("company", company)
        try:
            return EmployeeReview(**data)
        except Exception:
            return EmployeeReview(company=company, summary=str(data.get("summary", "")))


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
