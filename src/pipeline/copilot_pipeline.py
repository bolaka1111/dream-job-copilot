"""LangGraph StateGraph orchestrating the full Dream Job Copilot pipeline."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.agents.application_agent import ApplicationAgent
from src.agents.feedback_agent import FeedbackAgent
from src.agents.job_search_agent import JobSearchAgent
from src.agents.recommendation_agent import RecommendationAgent
from src.agents.resume_agent import ResumeAgent
from src.agents.resume_enhancement_agent import ResumeEnhancementAgent
from src.agents.review_agent import ReviewAgent
from src.config import get_settings
from src.models import (
    EnhancedResume,
    JobRole,
    PipelineState,
    UserFeedback,
)

console = Console()


# ---------------------------------------------------------------------------
# Node functions
# ---------------------------------------------------------------------------

def node_parse_resume(state: PipelineState) -> PipelineState:
    """Parse the resume file and analyse it with AI."""
    console.print(Panel("Stage 1 / 9 – Parsing & reviewing resume", style="bold blue"))
    agent = ResumeAgent()
    try:
        resume_data = agent.parse_and_review(state["resume_path"])
        return {**state, "resume_data": resume_data, "errors": state.get("errors", [])}
    except Exception as exc:
        errors = state.get("errors", []) + [f"parse_resume: {exc}"]
        return {**state, "errors": errors}


def node_search_jobs(state: PipelineState) -> PipelineState:
    """Search the job market based on resume data."""
    console.print(Panel("Stage 2 / 9 – Searching the job market", style="bold blue"))
    if not state.get("resume_data"):
        return {**state, "errors": state.get("errors", []) + ["search_jobs: no resume_data"]}

    agent = JobSearchAgent()
    try:
        jobs = agent.search_jobs(state["resume_data"])
        return {**state, "job_results": jobs}
    except Exception as exc:
        errors = state.get("errors", []) + [f"search_jobs: {exc}"]
        return {**state, "job_results": [], "errors": errors}


def node_recommend_roles(state: PipelineState) -> PipelineState:
    """Rank and recommend top-fit roles."""
    console.print(Panel("Stage 3 / 9 – Recommending best-fit roles", style="bold blue"))
    agent = RecommendationAgent()
    jobs = state.get("job_results") or []
    resume_data = state.get("resume_data")
    if not resume_data:
        return {**state, "recommendations": []}

    try:
        recommendations = agent.recommend_roles(resume_data, jobs)
        return {**state, "recommendations": recommendations}
    except Exception as exc:
        errors = state.get("errors", []) + [f"recommend_roles: {exc}"]
        return {**state, "recommendations": jobs[:5], "errors": errors}


def node_collect_feedback(state: PipelineState) -> PipelineState:
    """Collect interactive user feedback on recommendations."""
    console.print(Panel("Stage 4 / 9 – Collecting your feedback", style="bold blue"))
    recommendations = state.get("recommendations") or []

    if not state.get("interactive", True):
        # In non-interactive mode accept all recommendations
        feedback = UserFeedback(
            selected_role_indices=list(range(len(recommendations))),
        )
        return {**state, "user_feedback": feedback}

    agent = FeedbackAgent()
    try:
        feedback = agent.collect_feedback(recommendations)
        return {**state, "user_feedback": feedback}
    except Exception as exc:
        errors = state.get("errors", []) + [f"collect_feedback: {exc}"]
        feedback = UserFeedback(selected_role_indices=list(range(len(recommendations))))
        return {**state, "user_feedback": feedback, "errors": errors}


def node_refine_search(state: PipelineState) -> PipelineState:
    """Refine job search using user feedback and preferences."""
    console.print(Panel("Stage 5 / 9 – Refining search based on your feedback", style="bold blue"))
    feedback = state.get("user_feedback")
    resume_data = state.get("resume_data")

    if not feedback or not resume_data:
        return {**state, "refined_jobs": state.get("recommendations") or []}

    # Build a preference-aware search query and re-search
    agent = JobSearchAgent()
    try:
        # Patch resume target_roles with user's preferred industries/roles if provided
        import copy  # noqa: PLC0415
        refined_resume = copy.copy(resume_data)

        extra_queries: list[str] = []
        if feedback.preferred_industries:
            extra_queries.extend(feedback.preferred_industries)
        if feedback.preferred_locations:
            # Inject location into target roles to steer queries
            refined_resume = refined_resume.model_copy(
                update={
                    "target_roles": [
                        f"{r} in {feedback.preferred_locations[0]}"
                        for r in resume_data.target_roles
                    ]
                }
            )

        refined_jobs = agent.search_jobs(refined_resume)

        # Merge with original recommendations, keeping selected roles
        selected = [
            state["recommendations"][i]
            for i in (feedback.selected_role_indices or [])
            if i < len(state.get("recommendations") or [])
        ]
        merged = _deduplicate(selected + refined_jobs)
        return {**state, "refined_jobs": merged}
    except Exception as exc:
        errors = state.get("errors", []) + [f"refine_search: {exc}"]
        return {**state, "refined_jobs": state.get("recommendations") or [], "errors": errors}


def node_fetch_reviews(state: PipelineState) -> PipelineState:
    """Fetch employee reviews for shortlisted companies."""
    console.print(Panel("Stage 6 / 9 – Fetching employee reviews", style="bold blue"))
    jobs = state.get("refined_jobs") or state.get("recommendations") or []
    settings = get_settings()
    # Only fetch reviews for top N jobs to keep costs/time down
    top_jobs = sorted(jobs, key=lambda j: j.match_score, reverse=True)[
        : settings.max_shortlisted_jobs
    ]

    agent = ReviewAgent()
    try:
        reviewed = agent.fetch_reviews(top_jobs)
        return {**state, "reviewed_jobs": reviewed}
    except Exception as exc:
        errors = state.get("errors", []) + [f"fetch_reviews: {exc}"]
        # Wrap jobs with empty reviews as fallback
        from src.models import EmployeeReview  # noqa: PLC0415
        reviewed = [(j, EmployeeReview(company=j.company)) for j in top_jobs]
        return {**state, "reviewed_jobs": reviewed, "errors": errors}


def node_select_best_jobs(state: PipelineState) -> PipelineState:
    """Rank jobs by combined match score + employee rating."""
    console.print(Panel("Stage 7 / 9 – Selecting your dream job candidates", style="bold blue"))
    reviewed = state.get("reviewed_jobs") or []
    settings = get_settings()

    if not reviewed:
        return {**state, "shortlisted_jobs": []}

    # Combined score: 70% match_score + 30% normalised employee rating
    def combined(pair: tuple[JobRole, Any]) -> float:
        job, review = pair
        norm_rating = review.rating / 5.0 if review.rating else 0.0
        return 0.7 * job.match_score + 0.3 * norm_rating

    ranked = sorted(reviewed, key=combined, reverse=True)
    shortlisted = [job for job, _ in ranked[: settings.max_shortlisted_jobs]]

    _print_shortlist(shortlisted, ranked)
    return {**state, "shortlisted_jobs": shortlisted}


def node_enhance_resumes(state: PipelineState) -> PipelineState:
    """Tailor the resume for each shortlisted job."""
    console.print(Panel("Stage 8 / 9 – Enhancing resumes for each role", style="bold blue"))
    jobs = state.get("shortlisted_jobs") or []
    resume_data = state.get("resume_data")

    if not resume_data or not jobs:
        return {**state, "enhanced_resumes": []}

    agent = ResumeEnhancementAgent()
    enhanced: list[EnhancedResume] = []
    for job in jobs:
        try:
            enhanced_resume = agent.enhance_resume(resume_data, job)
            enhanced.append(enhanced_resume)
        except Exception as exc:
            errors = state.get("errors", []) + [f"enhance_resume({job.title}): {exc}"]
            state = {**state, "errors": errors}

    return {**state, "enhanced_resumes": enhanced}


def node_apply_to_jobs(state: PipelineState) -> PipelineState:
    """Submit (simulated) applications for each enhanced resume."""
    console.print(Panel("Stage 9 / 9 – Applying to dream jobs", style="bold blue"))
    enhanced_resumes = state.get("enhanced_resumes") or []

    if not enhanced_resumes:
        return {**state, "applications": []}

    agent = ApplicationAgent()
    applications = []
    for enhanced in enhanced_resumes:
        try:
            app = agent.apply_to_job(enhanced.job_role, enhanced)
            applications.append(app)
        except Exception as exc:
            errors = state.get("errors", []) + [f"apply_to_job: {exc}"]
            state = {**state, "errors": errors}

    return {**state, "applications": applications}


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def _build_graph() -> Any:
    """Construct and compile the LangGraph StateGraph."""
    graph = StateGraph(PipelineState)

    graph.add_node("parse_resume", node_parse_resume)
    graph.add_node("search_jobs", node_search_jobs)
    graph.add_node("recommend_roles", node_recommend_roles)
    graph.add_node("collect_feedback", node_collect_feedback)
    graph.add_node("refine_search", node_refine_search)
    graph.add_node("fetch_reviews", node_fetch_reviews)
    graph.add_node("select_best_jobs", node_select_best_jobs)
    graph.add_node("enhance_resumes", node_enhance_resumes)
    graph.add_node("apply_to_jobs", node_apply_to_jobs)

    graph.set_entry_point("parse_resume")

    graph.add_edge("parse_resume", "search_jobs")
    graph.add_edge("search_jobs", "recommend_roles")
    graph.add_edge("recommend_roles", "collect_feedback")
    graph.add_edge("collect_feedback", "refine_search")
    graph.add_edge("refine_search", "fetch_reviews")
    graph.add_edge("fetch_reviews", "select_best_jobs")
    graph.add_edge("select_best_jobs", "enhance_resumes")
    graph.add_edge("enhance_resumes", "apply_to_jobs")
    graph.add_edge("apply_to_jobs", END)

    return graph.compile()


# Singleton compiled graph
_compiled_graph = None


def _get_graph() -> Any:
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = _build_graph()
    return _compiled_graph


def run_pipeline(
    resume_path: str,
    interactive: bool = True,
    output_dir: str | None = None,
) -> dict[str, Any]:
    """Run the complete Dream Job Copilot pipeline.

    Args:
        resume_path: Path to the candidate's resume (PDF or DOCX).
        interactive: When True, pause to collect user feedback at stage 4.
        output_dir: Override the output directory for saved resumes.

    Returns:
        Final pipeline state as a plain dict.
    """
    if output_dir:
        # Temporarily patch settings (simple approach)
        import os  # noqa: PLC0415
        os.environ["OUTPUT_DIR"] = output_dir
        # Bust the settings cache
        get_settings.cache_clear()

    console.print(
        Panel(
            "[bold cyan]🚀 Dream Job Copilot[/bold cyan] – starting pipeline…",
            expand=False,
        )
    )

    initial_state: PipelineState = {
        "resume_path": resume_path,
        "interactive": interactive,
        "errors": [],
    }

    graph = _get_graph()
    final_state = graph.invoke(initial_state)

    _print_summary(final_state)
    return final_state


# ---------------------------------------------------------------------------
# Print helpers
# ---------------------------------------------------------------------------

def _print_shortlist(jobs: list[JobRole], ranked: list[tuple]) -> None:
    table = Table(title="🏆 Shortlisted Dream Jobs", header_style="bold green")
    table.add_column("Title", style="bold")
    table.add_column("Company")
    table.add_column("Match")
    table.add_column("Employee Rating")

    for job, review in ranked[: len(jobs)]:
        rating_str = f"{review.rating:.1f}/5" if review.rating else "N/A"
        table.add_row(
            job.title,
            job.company,
            f"{job.match_score:.0%}",
            rating_str,
        )
    console.print(table)


def _print_summary(state: dict) -> None:
    apps = state.get("applications") or []
    errors = state.get("errors") or []

    console.print(
        Panel(
            f"[bold green]✅ Pipeline complete![/bold green]\n"
            f"  Applications submitted: {len(apps)}\n"
            + (f"  Errors encountered:    {len(errors)}" if errors else ""),
            title="Summary",
            expand=False,
        )
    )

    if apps:
        table = Table(title="📬 Applications", header_style="bold")
        table.add_column("Role")
        table.add_column("Company")
        table.add_column("Resume File")
        for app in apps:
            table.add_row(
                app.job_role.title,
                app.job_role.company,
                app.output_file,
            )
        console.print(table)

    if errors:
        console.print("\n[yellow]⚠️  Errors:[/yellow]")
        for err in errors:
            console.print(f"  • {err}")


def _deduplicate(jobs: list[JobRole]) -> list[JobRole]:
    """Remove duplicate jobs by (title, company) keeping first occurrence."""
    seen: set[tuple[str, str]] = set()
    result: list[JobRole] = []
    for job in jobs:
        key = (job.title.lower(), job.company.lower())
        if key not in seen:
            seen.add(key)
            result.append(job)
    return result
