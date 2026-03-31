"""ApplicationAgent – save enhanced resumes and simulate job application submissions."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console

from src.config import get_settings
from src.models import EnhancedResume, JobApplication, JobRole

console = Console()


class ApplicationAgent:
    """Save tailored resumes to disk and record simulated job applications."""

    def __init__(self, output_dir: str | None = None) -> None:
        settings = get_settings()
        self._output_dir = Path(output_dir or settings.output_dir)

    def apply_to_job(
        self, job: JobRole, enhanced_resume: EnhancedResume
    ) -> JobApplication:
        """Persist the enhanced resume and create a :class:`JobApplication` record.

        For now this simulates an application (real form-fill would require
        Selenium/Playwright and is out of scope).  The enhanced resume is saved
        as a plain-text file ready for copy-paste or PDF conversion.
        """
        self._output_dir.mkdir(parents=True, exist_ok=True)

        filename = _safe_filename(job.company, job.title)
        output_path = self._output_dir / filename

        output_path.write_text(enhanced_resume.enhanced_text, encoding="utf-8")
        console.print(f"[green]💾 Resume saved:[/green] {output_path}")

        application = JobApplication(
            job_role=job,
            resume_used=enhanced_resume,
            application_status="submitted",
            applied_at=datetime.now(timezone.utc),
            output_file=str(output_path),
            notes=(
                f"Simulated application submitted for {job.title} at {job.company}. "
                f"Resume saved to {output_path}. "
                "To complete a real application, open the job URL and attach this resume."
            ),
        )

        _log_application(application, self._output_dir)
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


def _log_application(application: JobApplication, output_dir: Path) -> None:
    """Append a one-line summary to applications.log in *output_dir*."""
    log_path = output_dir / "applications.log"
    timestamp = application.applied_at.strftime("%Y-%m-%d %H:%M:%S")
    line = (
        f"{timestamp} | {application.job_role.title} | "
        f"{application.job_role.company} | {application.application_status} | "
        f"{application.output_file}\n"
    )
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(line)
