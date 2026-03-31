"""Integration tests for the full LangGraph pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.models import (
    EmployeeReview,
    EnhancedResume,
    JobApplication,
    JobRole,
    ResumeData,
    UserFeedback,
)


# ---------------------------------------------------------------------------
# Helpers – build fake agent return values
# ---------------------------------------------------------------------------

def _make_resume_data() -> ResumeData:
    return ResumeData(
        parsed_text="Jane Doe – Senior Software Engineer",
        skills=["Python", "Docker", "AWS"],
        experience_years=7.0,
        current_role="Senior Software Engineer",
        target_roles=["Staff Engineer"],
        review="Strong backend profile.",
    )


def _make_job_roles() -> list[JobRole]:
    return [
        JobRole(
            title="Staff Engineer",
            company="TechCorp",
            location="Remote",
            url="https://example.com/1",
            match_score=0.92,
            reasoning="Great fit.",
        ),
        JobRole(
            title="Principal Engineer",
            company="CloudCo",
            location="NYC",
            url="https://example.com/2",
            match_score=0.85,
            reasoning="AWS expertise.",
        ),
    ]


def _make_employee_review(company: str) -> EmployeeReview:
    return EmployeeReview(
        company=company,
        rating=4.2,
        pros=["Good culture"],
        cons=["Slow growth"],
        review_count=100,
        summary="Decent workplace.",
    )


def _make_enhanced_resume(job: JobRole) -> EnhancedResume:
    return EnhancedResume(
        original_text="original",
        enhanced_text=f"Enhanced for {job.title}",
        job_role=job,
        changes_summary="Added relevant keywords.",
    )


def _make_application(job: JobRole, enhanced: EnhancedResume) -> JobApplication:
    return JobApplication(
        job_role=job,
        resume_used=enhanced,
        application_status="submitted",
        output_file=f"/output/resume_{job.company}.txt",
    )


# ---------------------------------------------------------------------------
# Integration test – mock all agents
# ---------------------------------------------------------------------------

class TestRunPipeline:
    """Test run_pipeline with all agents mocked."""

    def _setup_mocks(self, tmp_path: Path) -> tuple[Path, dict]:
        """Create a dummy resume file and return (path, patch_targets dict)."""
        resume_path = tmp_path / "resume.pdf"
        resume_path.write_bytes(b"fake pdf")

        jobs = _make_job_roles()
        resume_data = _make_resume_data()
        reviews = [(j, _make_employee_review(j.company)) for j in jobs]
        enhanced = [_make_enhanced_resume(j) for j in jobs]
        applications = [_make_application(j, e) for j, e in zip(jobs, enhanced)]
        feedback = UserFeedback(selected_role_indices=[0, 1])

        return resume_path, {
            "resume_data": resume_data,
            "jobs": jobs,
            "reviews": reviews,
            "enhanced": enhanced,
            "applications": applications,
            "feedback": feedback,
        }

    def test_pipeline_returns_state_dict(self, tmp_path):
        resume_path, mocks = self._setup_mocks(tmp_path)

        mock_resume_agent = MagicMock()
        mock_resume_agent.parse_and_review.return_value = mocks["resume_data"]

        mock_job_agent = MagicMock()
        mock_job_agent.search_jobs.return_value = mocks["jobs"]

        mock_rec_agent = MagicMock()
        mock_rec_agent.recommend_roles.return_value = mocks["jobs"]

        mock_feedback_agent = MagicMock()
        mock_feedback_agent.collect_feedback.return_value = mocks["feedback"]

        mock_review_agent = MagicMock()
        mock_review_agent.fetch_reviews.return_value = mocks["reviews"]

        mock_enhance_agent = MagicMock()
        mock_enhance_agent.enhance_resume.side_effect = lambda rd, job: _make_enhanced_resume(job)

        mock_app_agent = MagicMock()
        mock_app_agent.apply_to_job.side_effect = lambda job, enhanced: _make_application(job, enhanced)

        with (
            patch("src.pipeline.copilot_pipeline.ResumeAgent", return_value=mock_resume_agent),
            patch("src.pipeline.copilot_pipeline.JobSearchAgent", return_value=mock_job_agent),
            patch("src.pipeline.copilot_pipeline.RecommendationAgent", return_value=mock_rec_agent),
            patch("src.pipeline.copilot_pipeline.FeedbackAgent", return_value=mock_feedback_agent),
            patch("src.pipeline.copilot_pipeline.ReviewAgent", return_value=mock_review_agent),
            patch("src.pipeline.copilot_pipeline.ResumeEnhancementAgent", return_value=mock_enhance_agent),
            patch("src.pipeline.copilot_pipeline.ApplicationAgent", return_value=mock_app_agent),
        ):
            from src.pipeline.copilot_pipeline import run_pipeline

            result = run_pipeline(
                resume_path=str(resume_path),
                interactive=False,
                output_dir=str(tmp_path / "output"),
            )

        assert isinstance(result, dict)
        assert result.get("resume_data") is not None
        assert isinstance(result.get("applications"), list)

    def test_pipeline_resume_agent_called(self, tmp_path):
        resume_path, mocks = self._setup_mocks(tmp_path)

        mock_resume_agent = MagicMock()
        mock_resume_agent.parse_and_review.return_value = mocks["resume_data"]

        mock_job_agent = MagicMock()
        mock_job_agent.search_jobs.return_value = []

        mock_rec_agent = MagicMock()
        mock_rec_agent.recommend_roles.return_value = []

        mock_feedback_agent = MagicMock()
        mock_feedback_agent.collect_feedback.return_value = UserFeedback()

        mock_review_agent = MagicMock()
        mock_review_agent.fetch_reviews.return_value = []

        mock_enhance_agent = MagicMock()
        mock_enhance_agent.enhance_resume.return_value = MagicMock()

        mock_app_agent = MagicMock()
        mock_app_agent.apply_to_job.return_value = MagicMock()

        with (
            patch("src.pipeline.copilot_pipeline.ResumeAgent", return_value=mock_resume_agent),
            patch("src.pipeline.copilot_pipeline.JobSearchAgent", return_value=mock_job_agent),
            patch("src.pipeline.copilot_pipeline.RecommendationAgent", return_value=mock_rec_agent),
            patch("src.pipeline.copilot_pipeline.FeedbackAgent", return_value=mock_feedback_agent),
            patch("src.pipeline.copilot_pipeline.ReviewAgent", return_value=mock_review_agent),
            patch("src.pipeline.copilot_pipeline.ResumeEnhancementAgent", return_value=mock_enhance_agent),
            patch("src.pipeline.copilot_pipeline.ApplicationAgent", return_value=mock_app_agent),
        ):
            from src.pipeline import copilot_pipeline

            # Reset the cached graph so it picks up fresh patches
            copilot_pipeline._compiled_graph = None
            result = copilot_pipeline.run_pipeline(
                resume_path=str(resume_path),
                interactive=False,
                output_dir=str(tmp_path / "output"),
            )

        mock_resume_agent.parse_and_review.assert_called_once_with(str(resume_path))

    def test_pipeline_non_interactive_skips_user_prompts(self, tmp_path):
        """In non-interactive mode feedback agent should NOT be called."""
        resume_path, mocks = self._setup_mocks(tmp_path)

        mock_resume_agent = MagicMock()
        mock_resume_agent.parse_and_review.return_value = mocks["resume_data"]

        mock_job_agent = MagicMock()
        mock_job_agent.search_jobs.return_value = mocks["jobs"]

        mock_rec_agent = MagicMock()
        mock_rec_agent.recommend_roles.return_value = mocks["jobs"]

        mock_feedback_agent = MagicMock()

        mock_review_agent = MagicMock()
        mock_review_agent.fetch_reviews.return_value = mocks["reviews"]

        mock_enhance_agent = MagicMock()
        mock_enhance_agent.enhance_resume.side_effect = lambda rd, job: _make_enhanced_resume(job)

        mock_app_agent = MagicMock()
        mock_app_agent.apply_to_job.side_effect = lambda job, e: _make_application(job, e)

        with (
            patch("src.pipeline.copilot_pipeline.ResumeAgent", return_value=mock_resume_agent),
            patch("src.pipeline.copilot_pipeline.JobSearchAgent", return_value=mock_job_agent),
            patch("src.pipeline.copilot_pipeline.RecommendationAgent", return_value=mock_rec_agent),
            patch("src.pipeline.copilot_pipeline.FeedbackAgent", return_value=mock_feedback_agent),
            patch("src.pipeline.copilot_pipeline.ReviewAgent", return_value=mock_review_agent),
            patch("src.pipeline.copilot_pipeline.ResumeEnhancementAgent", return_value=mock_enhance_agent),
            patch("src.pipeline.copilot_pipeline.ApplicationAgent", return_value=mock_app_agent),
        ):
            from src.pipeline import copilot_pipeline

            copilot_pipeline._compiled_graph = None
            copilot_pipeline.run_pipeline(
                resume_path=str(resume_path),
                interactive=False,
                output_dir=str(tmp_path / "output"),
            )

        # collect_feedback should not be called in non-interactive mode
        mock_feedback_agent.collect_feedback.assert_not_called()

    def test_pipeline_errors_collected(self, tmp_path):
        """Errors in nodes should be collected, not crash the pipeline."""
        resume_path = tmp_path / "resume.pdf"
        resume_path.write_bytes(b"fake")

        mock_resume_agent = MagicMock()
        mock_resume_agent.parse_and_review.side_effect = Exception("LLM API error")

        with patch("src.pipeline.copilot_pipeline.ResumeAgent", return_value=mock_resume_agent):
            from src.pipeline import copilot_pipeline

            copilot_pipeline._compiled_graph = None
            result = copilot_pipeline.run_pipeline(
                resume_path=str(resume_path),
                interactive=False,
                output_dir=str(tmp_path / "output"),
            )

        assert isinstance(result.get("errors"), list)
        assert len(result["errors"]) >= 1
        assert any("parse_resume" in e for e in result["errors"])
