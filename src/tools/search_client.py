"""Tavily-backed web and job search client."""

from __future__ import annotations

from typing import Any

from src.config import get_settings


class SearchClient:
    """Thin wrapper around TavilySearchResults for job and review searches."""

    def __init__(self) -> None:
        settings = get_settings()
        settings.validate_tavily_key()

        from langchain_community.tools.tavily_search import TavilySearchResults  # noqa: PLC0415

        self._tool = TavilySearchResults(
            api_key=settings.tavily_api_key,
            max_results=settings.max_job_results,
        )

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def search_jobs(self, query: str, max_results: int = 10) -> list[dict[str, Any]]:
        """Search for job postings matching *query*.

        Returns a list of raw result dicts with at least 'url', 'title', 'content'.
        """
        self._tool.max_results = max_results
        raw = self._tool.invoke({"query": query})
        return self._normalise(raw)

    def search_company_reviews(self, company: str) -> list[dict[str, Any]]:
        """Search for employee reviews for *company* on Glassdoor / Indeed / etc."""
        query = (
            f"{company} employee reviews Glassdoor site:glassdoor.com OR site:indeed.com "
            "pros cons rating"
        )
        self._tool.max_results = 5
        raw = self._tool.invoke({"query": query})
        return self._normalise(raw)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise(raw: Any) -> list[dict[str, Any]]:
        """Ensure the result is a plain list of dicts."""
        if isinstance(raw, list):
            return raw
        if isinstance(raw, str):
            # Tavily sometimes returns a JSON string
            import json  # noqa: PLC0415

            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
        return []
