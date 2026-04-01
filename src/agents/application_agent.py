"""ApplicationAgent – save enhanced resumes and simulate job application submissions.

Each agent is implemented as a LangGraph ReAct agent (create_react_agent) that
calls LangChain @tool-decorated functions to complete its work.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from rich.console import Console

from src.config import get_settings
from src.models import EnhancedResume, JobApplication, JobRole
from src.tools.llm_client import get_llm

console = Console()


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_APPLICATION_SYSTEM_PROMPT = """\
You are a job application assistant with access to file system tools.

Your task:
1. Use `save_resume_to_file` to persist the enhanced resume to disk.
2. Use `log_job_application_entry` to record the application in the log.
3. Return ONLY a valid JSON object:
{
  "output_file": "<path returned by save_resume_to_file>",
  "status": "submitted",
  "notes": "Brief note about the application"
}
"""


# ---------------------------------------------------------------------------
# Tool factories
# ---------------------------------------------------------------------------

def make_application_tools(output_dir: Path) -> list[Any]:
    """Return the list of LangChain tools for the application agent.

    Tools are closures that capture *output_dir* so they can write to disk
    without needing global state.
    """

    @tool
    def save_resume_to_file(company: str, job_title: str, resume_content: str) -> str:
        """Save an enhanced resume to a text file in the output directory.

        Args:
            company: Hiring company name (used in the filename).
            job_title: Job title being applied for (used in the filename).
            resume_content: Full text of the enhanced resume.

        Returns:
            Absolute path of the saved file.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = _safe_filename(company, job_title)
        output_path = output_dir / filename
        output_path.write_text(resume_content, encoding="utf-8")
        console.print(f"[green]💾 Resume saved:[/green] {output_path}")
        return str(output_path)

    @tool
    def log_job_application_entry(job_title: str, company: str, file_path: str) -> str:
        """Append a one-line application record to applications.log.

        Args:
            job_title: Title of the job being applied to.
            company: Hiring company name.
            file_path: Path to the saved resume file.

        Returns:
            Confirmation message.
        """
        log_path = output_dir / "applications.log"
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        line = f"{timestamp} | {job_title} | {company} | submitted | {file_path}\n"
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(line)
        return f"Application logged: {job_title} at {company}."

    return [save_resume_to_file, log_job_application_entry]


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------

def create_application_agent(llm: Any, output_dir: Path) -> Any:
    """Return a compiled LangGraph ReAct agent for saving resumes and logging applications."""
    tools = make_application_tools(output_dir)
    return create_react_agent(llm, tools=tools)


# ---------------------------------------------------------------------------
# Public class
# ---------------------------------------------------------------------------

class ApplicationAgent:
    """Save tailored resumes to disk and record simulated job applications."""

    def __init__(self, output_dir: str | None = None) -> None:
        settings = get_settings()
        self._output_dir = Path(output_dir or settings.output_dir)
        self._llm: Any = None
        self._agent: Any = None  # lazy-init

    def _get_agent(self) -> Any:
        if self._agent is None:
            llm = self._llm if self._llm is not None else get_llm(temperature=0.0)
            self._agent = create_application_agent(llm, self._output_dir)
        return self._agent

    def apply_to_job(
        self, job: JobRole, enhanced_resume: EnhancedResume
    ) -> JobApplication:
        """Persist the enhanced resume and create a :class:`JobApplication` record.

        The internal LangGraph ReAct agent calls ``save_resume_to_file`` and
        ``log_job_application_entry`` tools to complete the work.  Real form
        submission (Selenium / Playwright) is out of scope and left as a future
        extension.
        """
        agent = self._get_agent()

        prompt = (
            f"Apply to this job:\n"
            f"  Title: {job.title}\n"
            f"  Company: {job.company}\n\n"
            f"Enhanced resume content:\n---\n{enhanced_resume.enhanced_text}\n---\n\n"
            f"Save the resume and log the application, then return the JSON result."
        )

        result = agent.invoke(
            {
                "messages": [
                    SystemMessage(content=_APPLICATION_SYSTEM_PROMPT),
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

        data = _parse_json_object(str(last_content))
        output_file = data.get("output_file", "")
        notes = data.get(
            "notes",
            f"Simulated application submitted for {job.title} at {job.company}. "
            f"Resume saved to {output_file}. "
            "To complete a real application, open the job URL and attach this resume.",
        )

        application = JobApplication(
            job_role=job,
            resume_used=enhanced_resume,
            application_status="submitted",
            applied_at=datetime.now(timezone.utc),
            output_file=output_file,
            notes=notes,
        )

        console.print(
            f"[bold green]🚀 Applied (simulated):[/bold green] "
            f"{job.title} @ {job.company}"
        )
        return application


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_filename(company: str, title: str) -> str:
    """Return a filesystem-safe filename for a resume file."""
    def clean(s: str) -> str:
        return "".join(c if c.isalnum() or c in "-_ " else "_" for c in s).strip().replace(" ", "_")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"resume_{clean(company)}_{clean(title)}_{timestamp}.txt"


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
