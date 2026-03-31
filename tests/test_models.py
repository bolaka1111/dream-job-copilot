"""Tests for Pydantic data models."""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.models import (
    EmployeeReview,
    EnhancedResume,
    JobApplication,
    JobRole,
    PipelineState,
    ResumeData,
    UserFeedback,
)


class TestResumeData:
    def test_valid_instantiation(self, sample_resume_text):
        data = ResumeData(
            parsed_text=sample_resume_text,
            skills=["Python", "Go"],
            experience_years=5.0,
            education=["B.Sc. CS – MIT (2019)"],
            current_role="Software Engineer",
            target_roles=["Staff Engineer"],
        )
        assert data.experience_years == 5.0
        assert "Python" in data.skills

    def test_defaults_applied(self):
        data = ResumeData(parsed_text="some text")
        assert data.skills == []
        assert data.experience_years == 0.0
        assert data.education == []
        assert data.current_role == ""
        assert data.target_roles == []

    def test_experience_coercion_from_string(self):
        data = ResumeData(parsed_text="x", experience_years="3.5")
        assert data.experience_years == 3.5

    def test_experience_coercion_invalid(self):
        data = ResumeData(parsed_text="x", experience_years="not-a-number")
        assert data.experience_years == 0.0

    def test_negative_experience_rejected(self):
        with pytest.raises(ValidationError):
            ResumeData(parsed_text="x", experience_years=-1.0)

    def test_serialise_to_dict(self, sample_resume_data):
        d = sample_resume_data.model_dump()
        assert isinstance(d, dict)
        assert "parsed_text" in d
        assert "skills" in d
        assert isinstance(d["skills"], list)


class TestJobRole:
    def test_valid_instantiation(self):
        role = JobRole(title="Engineer", company="Acme")
        assert role.title == "Engineer"
        assert role.match_score == 0.0

    def test_match_score_clamped_high(self):
        role = JobRole(title="E", company="C", match_score=1.5)
        assert role.match_score == 1.0

    def test_match_score_clamped_low(self):
        role = JobRole(title="E", company="C", match_score=-0.5)
        assert role.match_score == 0.0

    def test_match_score_string_coercion(self):
        role = JobRole(title="E", company="C", match_score="0.75")
        assert role.match_score == 0.75

    def test_required_fields_missing(self):
        with pytest.raises(ValidationError):
            JobRole(company="Acme")  # title is required

    def test_serialise_to_dict(self, sample_job_roles):
        d = sample_job_roles[0].model_dump()
        assert d["title"] == "Staff Software Engineer"
        assert d["company"] == "TechCorp"
        assert isinstance(d["match_score"], float)


class TestEmployeeReview:
    def test_valid_instantiation(self):
        review = EmployeeReview(company="Acme", rating=4.5)
        assert review.rating == 4.5

    def test_rating_clamped(self):
        review = EmployeeReview(company="Acme", rating=6.0)
        assert review.rating == 5.0

    def test_rating_clamped_low(self):
        review = EmployeeReview(company="Acme", rating=-1.0)
        assert review.rating == 0.0

    def test_defaults(self):
        review = EmployeeReview(company="Acme")
        assert review.pros == []
        assert review.cons == []
        assert review.review_count == 0

    def test_negative_review_count_rejected(self):
        with pytest.raises(ValidationError):
            EmployeeReview(company="Acme", review_count=-5)

    def test_serialise(self, sample_employee_review):
        d = sample_employee_review.model_dump()
        assert d["company"] == "TechCorp"
        assert isinstance(d["pros"], list)


class TestEnhancedResume:
    def test_valid_instantiation(self, sample_resume_data, sample_job_roles):
        enhanced = EnhancedResume(
            original_text="original",
            enhanced_text="enhanced",
            job_role=sample_job_roles[0],
        )
        assert enhanced.job_role.company == "TechCorp"
        assert enhanced.changes_summary == ""

    def test_serialise(self, sample_resume_data, sample_job_roles):
        enhanced = EnhancedResume(
            original_text="orig",
            enhanced_text="enh",
            job_role=sample_job_roles[0],
            changes_summary="Added AWS keywords",
        )
        d = enhanced.model_dump()
        assert d["changes_summary"] == "Added AWS keywords"
        assert d["job_role"]["title"] == "Staff Software Engineer"


class TestJobApplication:
    def test_valid_instantiation(self, sample_job_roles):
        role = sample_job_roles[0]
        enhanced = EnhancedResume(
            original_text="orig", enhanced_text="enh", job_role=role
        )
        app = JobApplication(job_role=role, resume_used=enhanced)
        assert app.application_status == "submitted"
        assert isinstance(app.applied_at, datetime)

    def test_serialise(self, sample_job_roles):
        role = sample_job_roles[0]
        enhanced = EnhancedResume(original_text="o", enhanced_text="e", job_role=role)
        app = JobApplication(job_role=role, resume_used=enhanced)
        d = app.model_dump()
        assert "applied_at" in d
        assert d["application_status"] == "submitted"


class TestUserFeedback:
    def test_defaults(self):
        fb = UserFeedback()
        assert fb.selected_role_indices == []
        assert fb.preferred_industries == []
        assert fb.remote_preference is None

    def test_full(self):
        fb = UserFeedback(
            selected_role_indices=[0, 2],
            preferred_industries=["FinTech"],
            preferred_locations=["NYC"],
            remote_preference="hybrid",
            salary_expectation="$130k-$160k",
            additional_notes="Love Python shops",
        )
        assert fb.remote_preference == "hybrid"
        assert len(fb.selected_role_indices) == 2


class TestPipelineState:
    def test_is_typed_dict(self):
        state: PipelineState = {
            "resume_path": "/path/to/resume.pdf",
            "interactive": True,
            "errors": [],
        }
        assert state["resume_path"] == "/path/to/resume.pdf"

    def test_partial_state(self):
        state: PipelineState = {"errors": []}
        assert "resume_data" not in state
