"""
Python bridge script for the Express.js server.

This script is spawned as a child process by the Node.js server.
It runs pipeline stages and outputs JSON messages to stdout
that the Node.js server parses and broadcasts via SSE.

Usage:
  python run_pipeline.py --resume <path> --output-dir <dir> --mode initial
  python run_pipeline.py --resume <path> --output-dir <dir> --mode refine --feedback-file <path> --state-file <path>
  python run_pipeline.py --resume <path> --output-dir <dir> --mode apply --state-file <path>
  python run_pipeline.py --mode cover-letter --state-file <path> --job-index <N> --tone <tone> --length <length>
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure the project root is on the Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env into os.environ EARLY — before any library that reads env vars
# (e.g. Tavily, OpenAI SDKs check os.environ directly)
_env_file = PROJECT_ROOT / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _key, _, _val = _line.partition("=")
            os.environ.setdefault(_key.strip(), _val.strip())


def emit(msg: dict) -> None:
    """Write a JSON message to stdout for the Node.js bridge."""
    print(json.dumps(msg), flush=True)


def run_initial(resume_path: str, output_dir: str, dream_role: str = "", search_scope: str = "global") -> None:
    """Run stages 1-3: parse resume, search jobs, recommend roles."""
    os.environ.setdefault("OUTPUT_DIR", output_dir)
    os.makedirs(output_dir, exist_ok=True)

    from src.config import get_settings
    get_settings.cache_clear()

    state = {"resume_path": resume_path, "interactive": False, "errors": []}

    # Stage 1 — Parse resume
    emit({"type": "stage_start", "stage": 1, "stageName": "parse_resume"})
    try:
        from src.agents.resume_agent import ResumeAgent
        agent = ResumeAgent()
        resume_data = agent.parse_and_review(resume_path)
        state["resume_data"] = resume_data
        emit({
            "type": "stage_complete",
            "stage": 1,
            "stageName": "parse_resume",
            "data": {"resumeProfile": resume_data.model_dump()},
        })
    except Exception as exc:
        state["errors"].append(f"parse_resume: {exc}")
        emit({"type": "error", "stage": 1, "message": str(exc)})
        return

    # Stage 2 — Search jobs
    emit({"type": "stage_start", "stage": 2, "stageName": "search_jobs"})
    try:
        from src.agents.job_search_agent import JobSearchAgent
        agent = JobSearchAgent()
        jobs = agent.search_jobs(state["resume_data"])
        state["job_results"] = jobs
        emit({
            "type": "stage_complete",
            "stage": 2,
            "stageName": "search_jobs",
            "data": {"jobResults": [j.model_dump() for j in jobs]},
        })
    except Exception as exc:
        state["errors"].append(f"search_jobs: {exc}")
        state["job_results"] = []
        emit({"type": "error", "stage": 2, "message": str(exc)})

    # Stage 3 — Recommend roles
    emit({"type": "stage_start", "stage": 3, "stageName": "recommend_roles"})
    try:
        from src.agents.recommendation_agent import RecommendationAgent
        agent = RecommendationAgent()
        resume_data = state.get("resume_data")
        jobs = state.get("job_results", [])
        recommendations = agent.recommend_roles(resume_data, jobs) if resume_data else jobs[:5]
        state["recommendations"] = recommendations
        emit({
            "type": "stage_complete",
            "stage": 3,
            "stageName": "recommend_roles",
            "data": {"recommendations": [r.model_dump() for r in recommendations]},
        })
    except Exception as exc:
        state["errors"].append(f"recommend_roles: {exc}")
        jobs = state.get("job_results", [])
        state["recommendations"] = jobs[:5]
        emit({"type": "error", "stage": 3, "message": str(exc)})

    # Save state for later stages
    save_state(state, output_dir)

    emit({
        "type": "pipeline_complete",
        "stage": 3,
        "data": {
            "resumeProfile": state.get("resume_data").model_dump() if state.get("resume_data") else None,
            "jobResults": [j.model_dump() for j in state.get("job_results", [])],
            "recommendations": [r.model_dump() for r in state.get("recommendations", [])],
            "errors": state.get("errors", []),
        },
    })


def run_refine(resume_path: str, output_dir: str, feedback_file: str, state_file: str) -> None:
    """Run stages 5-7: refine search, fetch reviews, select best jobs."""
    state = load_state(state_file)
    feedback_data = json.loads(Path(feedback_file).read_text())

    os.environ.setdefault("OUTPUT_DIR", output_dir)
    from src.config import get_settings
    get_settings.cache_clear()

    from src.models import UserFeedback, JobRole
    feedback = UserFeedback(
        selected_role_indices=feedback_data.get("selected_role_indices", []),
        preferred_industries=feedback_data.get("preferred_industries", []),
        preferred_locations=feedback_data.get("preferred_locations", []),
        remote_preference=feedback_data.get("remote_preference"),
        salary_expectation=feedback_data.get("salary_expectation"),
        additional_notes=feedback_data.get("additional_notes", ""),
    )
    state["user_feedback"] = feedback

    # Stage 5 — Refine search
    emit({"type": "stage_start", "stage": 5, "stageName": "refine_search"})
    try:
        from src.agents.job_search_agent import JobSearchAgent
        import copy
        resume_data = state.get("resume_data")
        if resume_data and feedback.preferred_locations:
            resume_data = resume_data.model_copy(
                update={"target_roles": [f"{r} in {feedback.preferred_locations[0]}" for r in resume_data.target_roles]}
            )

        agent = JobSearchAgent()
        refined_jobs = agent.search_jobs(resume_data) if resume_data else []

        # Merge with selected recommendations
        recommendations = state.get("recommendations", [])
        selected = [recommendations[i] for i in feedback.selected_role_indices if i < len(recommendations)]

        seen = set()
        merged = []
        for job in selected + refined_jobs:
            key = (job.title.lower(), job.company.lower())
            if key not in seen:
                seen.add(key)
                merged.append(job)

        state["refined_jobs"] = merged
        emit({
            "type": "stage_complete",
            "stage": 5,
            "stageName": "refine_search",
            "data": {"refinedJobs": [j.model_dump() for j in merged]},
        })
    except Exception as exc:
        state["errors"] = state.get("errors", []) + [f"refine_search: {exc}"]
        state["refined_jobs"] = state.get("recommendations", [])
        emit({"type": "error", "stage": 5, "message": str(exc)})

    # Stage 6 — Fetch reviews
    emit({"type": "stage_start", "stage": 6, "stageName": "fetch_reviews"})
    try:
        from src.agents.review_agent import ReviewAgent
        settings = get_settings()
        jobs = state.get("refined_jobs", [])
        top_jobs = sorted(jobs, key=lambda j: j.match_score, reverse=True)[:settings.max_shortlisted_jobs]

        agent = ReviewAgent()
        reviewed = agent.fetch_reviews(top_jobs)
        state["reviewed_jobs"] = reviewed
        emit({
            "type": "stage_complete",
            "stage": 6,
            "stageName": "fetch_reviews",
            "data": {"reviews": [{"job": j.model_dump(), "review": r.model_dump()} for j, r in reviewed]},
        })
    except Exception as exc:
        state["errors"] = state.get("errors", []) + [f"fetch_reviews: {exc}"]
        from src.models import EmployeeReview
        jobs = state.get("refined_jobs", state.get("recommendations", []))
        settings = get_settings()
        top_jobs = sorted(jobs, key=lambda j: j.match_score, reverse=True)[:settings.max_shortlisted_jobs]
        reviewed = [(j, EmployeeReview(company=j.company)) for j in top_jobs]
        state["reviewed_jobs"] = reviewed
        emit({"type": "error", "stage": 6, "message": str(exc)})

    # Stage 7 — Select best jobs
    emit({"type": "stage_start", "stage": 7, "stageName": "select_best_jobs"})
    try:
        reviewed = state.get("reviewed_jobs", [])
        settings = get_settings()

        def combined(pair):
            job, review = pair
            norm_rating = review.rating / 5.0 if review.rating else 0.0
            return 0.7 * job.match_score + 0.3 * norm_rating

        ranked = sorted(reviewed, key=combined, reverse=True)
        shortlisted = [job for job, _ in ranked[:settings.max_shortlisted_jobs]]
        state["shortlisted_jobs"] = shortlisted

        emit({
            "type": "stage_complete",
            "stage": 7,
            "stageName": "select_best_jobs",
            "data": {
                "bestJobs": [j.model_dump() for j in shortlisted],
                "reviewedJobs": [{"job": j.model_dump(), "review": r.model_dump()} for j, r in ranked[:settings.max_shortlisted_jobs]],
            },
        })
    except Exception as exc:
        state["errors"] = state.get("errors", []) + [f"select_best_jobs: {exc}"]
        emit({"type": "error", "stage": 7, "message": str(exc)})

    save_state(state, output_dir)
    emit({"type": "pipeline_complete", "stage": 7})


def run_apply(output_dir: str, state_file: str) -> None:
    """Run stages 8-9: enhance resumes and apply to jobs."""
    state = load_state(state_file)

    os.environ.setdefault("OUTPUT_DIR", output_dir)
    from src.config import get_settings
    get_settings.cache_clear()

    # Stage 8 — Enhance resumes
    emit({"type": "stage_start", "stage": 8, "stageName": "enhance_resumes"})
    try:
        from src.agents.resume_enhancement_agent import ResumeEnhancementAgent
        jobs = state.get("shortlisted_jobs", [])
        resume_data = state.get("resume_data")

        if not resume_data or not jobs:
            state["enhanced_resumes"] = []
        else:
            agent = ResumeEnhancementAgent()
            enhanced = []
            for job in jobs:
                try:
                    er = agent.enhance_resume(resume_data, job)
                    enhanced.append(er)
                except Exception as exc:
                    state["errors"] = state.get("errors", []) + [f"enhance_resume({job.title}): {exc}"]
            state["enhanced_resumes"] = enhanced

        emit({
            "type": "stage_complete",
            "stage": 8,
            "stageName": "enhance_resumes",
            "data": {"enhancedResumes": [e.model_dump() for e in state.get("enhanced_resumes", [])]},
        })
    except Exception as exc:
        state["errors"] = state.get("errors", []) + [f"enhance_resumes: {exc}"]
        emit({"type": "error", "stage": 8, "message": str(exc)})

    # Stage 9 — Apply to jobs
    emit({"type": "stage_start", "stage": 9, "stageName": "apply_to_jobs"})
    try:
        from src.agents.application_agent import ApplicationAgent
        enhanced_resumes = state.get("enhanced_resumes", [])

        if not enhanced_resumes:
            state["applications"] = []
        else:
            agent = ApplicationAgent()
            applications = []
            for er in enhanced_resumes:
                try:
                    app = agent.apply_to_job(er.job_role, er)
                    applications.append(app)
                except Exception as exc:
                    state["errors"] = state.get("errors", []) + [f"apply_to_job: {exc}"]
            state["applications"] = applications

        emit({
            "type": "stage_complete",
            "stage": 9,
            "stageName": "apply_to_jobs",
            "data": {"applications": [a.model_dump(mode="json") for a in state.get("applications", [])]},
        })
    except Exception as exc:
        state["errors"] = state.get("errors", []) + [f"apply_to_jobs: {exc}"]
        emit({"type": "error", "stage": 9, "message": str(exc)})

    save_state(state, output_dir)
    emit({"type": "pipeline_complete", "stage": 9})


def run_cover_letter(state_file: str, job_index: int, tone: str, length: str) -> None:
    """Generate a single cover letter for a specific job."""
    state = load_state(state_file)
    jobs = state.get("shortlisted_jobs", [])

    if job_index < 0 or job_index >= len(jobs):
        emit({"type": "error", "message": f"Invalid job index: {job_index}"})
        return

    job = jobs[job_index]
    resume_data = state.get("resume_data")

    if not resume_data:
        emit({"type": "error", "message": "No resume data available"})
        return

    from src.tools.llm_client import get_llm
    from langchain_core.messages import HumanMessage, SystemMessage

    length_words = {"short": 200, "standard": 350, "long": 500}.get(length, 350)

    llm = get_llm(temperature=0.4)
    messages = [
        SystemMessage(content=(
            f"You are an expert career coach. Write a {tone} cover letter of approximately "
            f"{length_words} words for the following job. Tailor it to the candidate's resume. "
            f"Do NOT include placeholder brackets. Output ONLY the cover letter text."
        )),
        HumanMessage(content=(
            f"Job Title: {job.title}\n"
            f"Company: {job.company}\n"
            f"Location: {job.location}\n"
            f"Description: {job.description}\n\n"
            f"Candidate Skills: {', '.join(resume_data.skills)}\n"
            f"Experience: {resume_data.experience_years} years\n"
            f"Current Role: {resume_data.current_role}\n"
            f"Resume:\n{resume_data.parsed_text[:2000]}"
        )),
    ]

    response = llm.invoke(messages)
    emit({"cover_letter": response.content})


# --- State persistence helpers ---

def save_state(state: dict, output_dir: str) -> None:
    """Save pipeline state to a JSON file for inter-stage persistence."""
    os.makedirs(output_dir, exist_ok=True)
    state_file = os.path.join(output_dir, "pipeline_state.json")

    serializable = {}
    for key, val in state.items():
        if hasattr(val, "model_dump"):
            serializable[key] = val.model_dump()
        elif isinstance(val, list) and val and hasattr(val[0], "model_dump"):
            serializable[key] = [v.model_dump() if hasattr(v, "model_dump") else v for v in val]
        elif isinstance(val, list) and val and isinstance(val[0], tuple):
            # reviewed_jobs: list[tuple[JobRole, EmployeeReview]]
            serializable[key] = [
                {"job": a.model_dump() if hasattr(a, "model_dump") else a,
                 "review": b.model_dump() if hasattr(b, "model_dump") else b}
                for a, b in val
            ]
        else:
            serializable[key] = val

    with open(state_file, "w") as f:
        json.dump(serializable, f, indent=2, default=str)


def load_state(state_file: str) -> dict:
    """Load pipeline state from JSON and rehydrate Pydantic models."""
    with open(state_file) as f:
        raw = json.load(f)

    from src.models import ResumeData, JobRole, EmployeeReview, EnhancedResume, JobApplication

    state = {}
    state["errors"] = raw.get("errors", [])
    state["resume_path"] = raw.get("resume_path", "")
    state["interactive"] = raw.get("interactive", False)

    if raw.get("resume_data"):
        state["resume_data"] = ResumeData(**raw["resume_data"])

    if raw.get("job_results"):
        state["job_results"] = [JobRole(**j) for j in raw["job_results"]]

    if raw.get("recommendations"):
        state["recommendations"] = [JobRole(**j) for j in raw["recommendations"]]

    if raw.get("refined_jobs"):
        state["refined_jobs"] = [JobRole(**j) for j in raw["refined_jobs"]]

    if raw.get("reviewed_jobs"):
        state["reviewed_jobs"] = [
            (JobRole(**item["job"]), EmployeeReview(**item["review"]))
            for item in raw["reviewed_jobs"]
        ]

    if raw.get("shortlisted_jobs"):
        state["shortlisted_jobs"] = [JobRole(**j) for j in raw["shortlisted_jobs"]]

    if raw.get("enhanced_resumes"):
        state["enhanced_resumes"] = [EnhancedResume(**e) for e in raw["enhanced_resumes"]]

    if raw.get("applications"):
        state["applications"] = [JobApplication(**a) for a in raw["applications"]]

    if raw.get("user_feedback"):
        from src.models import UserFeedback
        state["user_feedback"] = UserFeedback(**raw["user_feedback"])

    return state


def main():
    parser = argparse.ArgumentParser(description="Dream Job Copilot — pipeline bridge")
    parser.add_argument("--resume", default="")
    parser.add_argument("--output-dir", default="./output")
    parser.add_argument("--mode", required=True, choices=["initial", "refine", "apply", "cover-letter"])
    parser.add_argument("--feedback-file", default="")
    parser.add_argument("--state-file", default="")
    parser.add_argument("--dream-role", default="")
    parser.add_argument("--search-scope", default="global")
    parser.add_argument("--job-index", type=int, default=0)
    parser.add_argument("--tone", default="professional")
    parser.add_argument("--length", default="standard")
    args = parser.parse_args()

    try:
        if args.mode == "initial":
            run_initial(args.resume, args.output_dir, args.dream_role, args.search_scope)
        elif args.mode == "refine":
            run_refine(args.resume, args.output_dir, args.feedback_file, args.state_file)
        elif args.mode == "apply":
            run_apply(args.output_dir, args.state_file)
        elif args.mode == "cover-letter":
            run_cover_letter(args.state_file, args.job_index, args.tone, args.length)
    except Exception as exc:
        emit({"type": "error", "message": str(exc)})
        sys.exit(1)


if __name__ == "__main__":
    main()
