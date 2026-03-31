"""FeedbackAgent – interactively collect user preferences on recommended roles."""

from __future__ import annotations

from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from src.models import JobRole, UserFeedback

console = Console()


class FeedbackAgent:
    """Display recommended roles and collect structured feedback from the user."""

    def collect_feedback(self, recommendations: list[JobRole]) -> UserFeedback:
        """Render roles in a Rich table and prompt the user for preferences.

        Returns a :class:`UserFeedback` instance populated from user input.
        In non-interactive contexts (e.g. tests) the prompts can be bypassed
        by patching ``input`` / the Rich prompt functions.
        """
        if not recommendations:
            console.print("[yellow]No recommendations to display.[/yellow]")
            return UserFeedback()

        self._display_recommendations(recommendations)

        # --- Which roles do you like? ---
        selected_indices = self._prompt_role_selection(recommendations)

        # --- Additional preferences ---
        industries = self._prompt_list("Preferred industries (comma-separated, or Enter to skip)")
        locations = self._prompt_list("Preferred locations (comma-separated, or Enter to skip)")

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

        feedback = UserFeedback(
            selected_role_indices=selected_indices,
            preferred_industries=industries,
            preferred_locations=locations,
            remote_preference=remote_pref,
            salary_expectation=salary,
            additional_notes=notes,
        )
        console.print("[green]✅ Feedback recorded.[/green]")
        return feedback

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _display_recommendations(self, roles: list[JobRole]) -> None:
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

        for i, role in enumerate(roles, start=1):
            score_str = f"{role.match_score:.0%}"
            table.add_row(
                str(i),
                role.title,
                role.company,
                role.location or "—",
                score_str,
                role.reasoning[:80] + "…" if len(role.reasoning) > 80 else role.reasoning,
            )

        console.print(table)

    def _prompt_role_selection(self, roles: list[JobRole]) -> list[int]:
        """Ask the user to select roles by number. Returns 0-based indices."""
        console.print(
            "\nEnter the [bold]numbers[/bold] of roles you're interested in "
            "(comma-separated, e.g. 1,3), or [bold]Enter[/bold] to accept all:"
        )
        raw = Prompt.ask("Your selection", default="").strip()
        if not raw:
            return list(range(len(roles)))

        selected: list[int] = []
        for part in raw.split(","):
            part = part.strip()
            if part.isdigit():
                idx = int(part) - 1  # convert to 0-based
                if 0 <= idx < len(roles):
                    selected.append(idx)
        return selected or list(range(len(roles)))

    @staticmethod
    def _prompt_list(prompt: str) -> list[str]:
        raw = Prompt.ask(prompt, default="").strip()
        if not raw:
            return []
        return [item.strip() for item in raw.split(",") if item.strip()]
