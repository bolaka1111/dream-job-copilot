"""Pydantic v2 data models for all pipeline states and entities."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator
from typing_extensions import TypedDict


class ResumeData(BaseModel):
    """Parsed and analysed resume data."""

    parsed_text: str = Field(description="Raw text extracted from the resume file")
    skills: list[str] = Field(default_factory=list, description="Technical and soft skills")
    experience_years: float = Field(default=0.0, ge=0, description="Total years of experience")
    education: list[str] = Field(default_factory=list, description="Degrees / certifications")
    current_role: str = Field(default="", description="Most recent job title")
    target_roles: list[str] = Field(default_factory=list, description="Desired job titles")
    review: str = Field(default="", description="AI-generated resume review / analysis")

    @field_validator("experience_years", mode="before")
    @classmethod
    def coerce_experience(cls, v: Any) -> float:
        try:
            return float(v)
        except (TypeError, ValueError):
            return 0.0


class JobRole(BaseModel):
    """A job posting or role discovered during search."""

    title: str = Field(description="Job title")
    company: str = Field(description="Hiring company name")
    location: str = Field(default="", description="Job location or 'Remote'")
    url: str = Field(default="", description="Link to the job posting")
    description: str = Field(default="", description="Job description snippet")
    match_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Relevance score (0-1)"
    )
    source: str = Field(default="", description="Source of the job listing")
    reasoning: str = Field(default="", description="Why this role was recommended")

    @field_validator("match_score", mode="before")
    @classmethod
    def clamp_score(cls, v: Any) -> float:
        try:
            return max(0.0, min(1.0, float(v)))
        except (TypeError, ValueError):
            return 0.0


class EmployeeReview(BaseModel):
    """Aggregated employee review data for a company."""

    company: str = Field(description="Company name")
    rating: float = Field(
        default=0.0, ge=0.0, le=5.0, description="Average employee rating (0-5)"
    )
    pros: list[str] = Field(default_factory=list, description="Positive aspects")
    cons: list[str] = Field(default_factory=list, description="Negative aspects")
    review_count: int = Field(default=0, ge=0, description="Number of reviews sampled")
    summary: str = Field(default="", description="AI-generated summary of reviews")

    @field_validator("rating", mode="before")
    @classmethod
    def clamp_rating(cls, v: Any) -> float:
        try:
            return max(0.0, min(5.0, float(v)))
        except (TypeError, ValueError):
            return 0.0


class EnhancedResume(BaseModel):
    """Resume tailored for a specific job role."""

    original_text: str = Field(description="Original resume text")
    enhanced_text: str = Field(description="AI-enhanced resume text for the target role")
    job_role: JobRole = Field(description="Target job role this resume is tailored for")
    changes_summary: str = Field(
        default="", description="Summary of changes made to the resume"
    )


class JobApplication(BaseModel):
    """Record of a job application submission."""

    job_role: JobRole = Field(description="Job role applied to")
    resume_used: EnhancedResume = Field(description="Enhanced resume used for this application")
    application_status: str = Field(
        default="submitted", description="Status of the application"
    )
    applied_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of application",
    )
    output_file: str = Field(default="", description="Path to saved resume file")
    notes: str = Field(default="", description="Additional notes about the application")


class UserFeedback(BaseModel):
    """Structured feedback collected from the user."""

    selected_role_indices: list[int] = Field(
        default_factory=list, description="Indices of roles the user liked"
    )
    preferred_industries: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    remote_preference: Optional[str] = Field(
        default=None, description="'remote', 'hybrid', 'onsite', or None"
    )
    salary_expectation: Optional[str] = Field(default=None, description="Expected salary range")
    additional_notes: str = Field(default="")


# ---------------------------------------------------------------------------
# LangGraph state – TypedDict so LangGraph can merge keys across nodes
# ---------------------------------------------------------------------------

class PipelineState(TypedDict, total=False):
    """Shared state passed through every LangGraph node."""

    resume_path: str
    interactive: bool
    resume_data: Optional[ResumeData]
    job_results: Optional[list[JobRole]]
    recommendations: Optional[list[JobRole]]
    user_feedback: Optional[UserFeedback]
    refined_jobs: Optional[list[JobRole]]
    reviewed_jobs: Optional[list[tuple[JobRole, EmployeeReview]]]
    shortlisted_jobs: Optional[list[JobRole]]
    enhanced_resumes: Optional[list[EnhancedResume]]
    applications: Optional[list[JobApplication]]
    errors: list[str]
