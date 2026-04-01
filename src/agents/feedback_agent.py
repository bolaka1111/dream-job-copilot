"""FeedbackAgent – interactively collect user preferences on recommended roles.

Each agent is implemented as a LangGraph ReAct agent (create_react_agent) that
calls LangChain @tool-decorated functions to complete its work.
"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from src.models import JobRole, UserFeedback
from src.tools.llm_client import get_llm

console = Console()


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool
def display_job_recommendations(jobs_json: str) -> str:
    """Display a formatted table of job recommendations to the user.

    Args:
        jobs_json: JSON array of job objects with title, company, location,
            match_score, and reasoning fields.

    Returns:
        Confirmation string indicating how many roles were displayed.
    """
    try:
        jobs_data: list[dict[str, Any]] = json.loads(jobs_json)
    except (json.JSONDecodeError, TypeError):
        jobs_data = []

    table = Table(
        title="🎯 Recommended Roles",
        show_header=True,
        header_style="bold magenta",
        expand=True,
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Title", style="bold")
    table.add_column("Company")
    table.add_column("Location")
    table.add_column("Score", justify="right")
    table.add_column("Why", overflow="fold")

    for i, job in enumerate(jobs_data, start=1):
        score = job.get("match_score", 0.0)
        score_str = f"{float(score):.0%}"
        reasoning = job.get("reasoning", "")
        short_reason = reasoning[:80] + "…" if len(reasoning) > 80 else reasoning
        table.add_row(
            str(i),
            job.get("title", ""),
            job.get("company", ""),
            job.get("location", "—"),
            score_str,
            short_reason,
        )

    console.print(table)
    return f"Displayed {len(jobs_data)} job recommendations."


@tool
def get_user_role_selection(num_available: int) -> str:
    """Prompt the user to select which job roles they are interested in.

    Args:
        num_available: Total number of roles shown in the table.

    Returns:
        JSON object with a ``selected_indices`` key (0-based list of ints).
    """
    console.print(
        "\nEnter the [bold]numbers[/bold] of roles you're interested in "
        "(comma-separated, e.g. 1,3), or [bold]Enter[/bold] to accept all:"
    )
    raw = Prompt.ask("Your selection", default="").strip()
    if not raw:
        return json.dumps({"selected_indices": list(range(num_available))})

    selected: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            idx = int(part) - 1  # convert to 0-based
            if 0 <= idx < num_available:
                selected.append(idx)
    if not selected:
        selected = list(range(num_available))
    return json.dumps({"selected_indices": selected})


@tool
def get_user_preferences() -> str:
    """Collect additional job search preferences from the user interactively.

    Returns:
        JSON object with preferred_industries, preferred_locations,
        remote_preference, salary_expectation, and additional_notes.
    """
    industries_raw = Prompt.ask(
        "Preferred industries (comma-separated, or Enter to skip)", default=""
    ).strip()
    industries = [i.strip() for i in industries_raw.split(",") if i.strip()]

    locations_raw = Prompt.ask(
        "Preferred locations (comma-separated, or Enter to skip)", default=""
    ).strip()
    locations = [loc.strip() for loc in locations_raw.split(",") if loc.strip()]

    remote_pref = Prompt.ask(
        "Remote preference",
        choices=["remote", "hybrid", "onsite", "any"],
        default="any",
    )
    remote_pref = None if remote_pref == "any" else remote_pref

    salary = Prompt.ask(
        "Expected salary range (e.g. '$100k-$130k', or Enter to skip)",
        default="",
    ).strip() or None

    notes = Prompt.ask(
        "Any other preferences or notes (or Enter to skip)",
        default="",
    ).strip()

    return json.dumps(
        {
            "preferred_industries": industries,
            "preferred_locations": locations,
            "remote_preference": remote_pref,
            "salary_expectation": salary,
            "additional_notes": notes,
        }
    )


# All tools exposed by this agent
FEEDBACK_TOOLS = [display_job_recommendations, get_user_role_selection, get_user_preferences]


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_FEEDBACK_SYSTEM_PROMPT = """\
You are a career coach assistant collecting feedback from a job candidate.

Your task (follow these steps IN ORDER):
1. Call `display_job_recommendations` with the jobs JSON to show the candidate their options.
2. Call `get_user_role_selection` with the number of available roles to record their picks.
3. Call `get_user_preferences` to capture industry, location, remote, salary, and notes.
4. Return ONLY a valid JSON object summarising all collected feedback:
{
  "selected_role_indices": [...],
  "preferred_industries": [...],
  "preferred_locations": [...],
  "remote_preference": "remote" | "hybrid" | "onsite" | null,
  "salary_expectation": "..." | null,
  "additional_notes": "..."
}
"""


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------

def create_feedback_agent(llm: Any) -> Any:
    """Return a compiled LangGraph ReAct agent for interactive feedback collection."""
    return create_react_agent(llm, tools=FEEDBACK_TOOLS)


# ---------------------------------------------------------------------------
# Public class
# ---------------------------------------------------------------------------

class FeedbackAgent:
    """Display recommended roles and collect structured feedback via a LangGraph ReAct agent."""

    def __init__(self, llm: Any = None) -> None:
        self._llm = llm
        self._agent: Any = None  # lazy-init

    def _get_agent(self) -> Any:
        if self._agent is None:
            llm = self._llm if self._llm is not None else get_llm(temperature=0.0)
            self._agent = create_feedback_agent(llm)
        return self._agent

    def collect_feedback(self, recommendations: list[JobRole]) -> UserFeedback:
        """Render roles in a Rich table, prompt the user, and return UserFeedback.

        The LangGraph ReAct agent drives the interaction by calling the
        ``display_job_recommendations``, ``get_user_role_selection``, and
        ``get_user_preferences`` tools in sequence.
        """
        if not recommendations:
            console.print("[yellow]No recommendations to display.[/yellow]")
            return UserFeedback()

        jobs_json = json.dumps([r.model_dump() for r in recommendations])

        agent = self._get_agent()
        result = agent.invoke(
            {
                "messages": [
                    SystemMessage(content=_FEEDBACK_SYSTEM_PROMPT),
                    HumanMessage(
                        content=(
                            f"Please collect feedback on these {len(recommendations)} "
                            f"job recommendations:\n{jobs_json}"
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

        feedback = UserFeedback(
            selected_role_indices=data.get(
                "selected_role_indices", list(range(len(recommendations)))
            ),
            preferred_industries=data.get("preferred_industries", []),
            preferred_locations=data.get("preferred_locations", []),
            remote_preference=data.get("remote_preference"),
            salary_expectation=data.get("salary_expectation"),
            additional_notes=data.get("additional_notes", ""),
        )
        console.print("[green]✅ Feedback recorded.[/green]")
        return feedback


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
    brace_match = re.search(r"\{[\s\S]+\}", text)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass
    return {}
