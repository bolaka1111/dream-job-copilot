"""Shared pytest fixtures for Dream Job Copilot tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.models import EmployeeReview, EnhancedResume, JobRole, ResumeData


@pytest.fixture
def sample_resume_text() -> str:
    return """
Jane Doe
Senior Software Engineer
jane.doe@email.com | github.com/janedoe | LinkedIn: /in/janedoe

SUMMARY
Results-driven software engineer with 7 years of experience building scalable
backend services and data pipelines. Passionate about distributed systems, cloud
architecture, and developer tooling.

EXPERIENCE
Senior Software Engineer – Acme Corp (2020 – Present)
- Led migration of monolith to microservices, reducing latency by 40%.
- Designed and maintained CI/CD pipelines using GitHub Actions and ArgoCD.
- Mentored 3 junior engineers; introduced TDD practices across the team.

Software Engineer – StartupXYZ (2017 – 2020)
- Built real-time data ingestion pipeline processing 5M events/day using Kafka + Spark.
- Reduced AWS infrastructure costs by 25% through resource optimisation.
- Developed REST APIs in Python (FastAPI) and Go consumed by 200k monthly active users.

SKILLS
Python, Go, Java, FastAPI, Django, Kafka, Spark, PostgreSQL, Redis, Docker,
Kubernetes, AWS (EC2, S3, Lambda, RDS), Terraform, GitHub Actions, Grafana,
System Design, Agile / Scrum, Leadership, Communication

EDUCATION
B.Sc. Computer Science – State University (2017)
AWS Certified Solutions Architect – Associate (2021)

PROJECTS
OpenMetrics (github.com/janedoe/openmetrics)
- Open-source metrics aggregation library with 1.2k GitHub stars.
""".strip()


@pytest.fixture
def sample_resume_data(sample_resume_text: str) -> ResumeData:
    return ResumeData(
        parsed_text=sample_resume_text,
        skills=[
            "Python", "Go", "Java", "FastAPI", "Kafka", "Spark",
            "PostgreSQL", "Redis", "Docker", "Kubernetes", "AWS", "Terraform",
        ],
        experience_years=7.0,
        education=[
            "B.Sc. Computer Science – State University (2017)",
            "AWS Certified Solutions Architect – Associate (2021)",
        ],
        current_role="Senior Software Engineer",
        target_roles=[
            "Staff Software Engineer",
            "Principal Engineer",
            "Engineering Manager",
        ],
        review=(
            "Strong backend profile with solid cloud and distributed systems experience. "
            "Resume highlights quantifiable achievements effectively. "
            "Consider adding more detail about leadership scope and business impact."
        ),
    )


@pytest.fixture
def sample_job_roles() -> list[JobRole]:
    return [
        JobRole(
            title="Staff Software Engineer",
            company="TechCorp",
            location="San Francisco, CA",
            url="https://techcorp.com/jobs/1",
            description="Build distributed systems and lead technical direction.",
            match_score=0.92,
            source="tavily",
            reasoning="Excellent match: distributed systems, Python, Kubernetes.",
        ),
        JobRole(
            title="Principal Engineer",
            company="CloudCo",
            location="Remote",
            url="https://cloudco.com/jobs/42",
            description="Architect cloud-native solutions on AWS.",
            match_score=0.85,
            source="tavily",
            reasoning="Strong alignment with AWS and microservices expertise.",
        ),
        JobRole(
            title="Engineering Manager",
            company="FinStartup",
            location="New York, NY",
            url="https://finstartup.com/jobs/7",
            description="Lead a team of 8 engineers building payment infrastructure.",
            match_score=0.78,
            source="tavily",
            reasoning="Leadership experience and backend expertise are a good fit.",
        ),
    ]


@pytest.fixture
def sample_employee_review() -> EmployeeReview:
    return EmployeeReview(
        company="TechCorp",
        rating=4.2,
        pros=["Great work-life balance", "Competitive pay", "Strong engineering culture"],
        cons=["Slow promotion cycles", "Too many meetings"],
        review_count=312,
        summary="TechCorp is highly rated for its engineering culture and compensation.",
    )


@pytest.fixture
def mock_llm() -> MagicMock:
    """A MagicMock that mimics a ChatOpenAI LLM."""
    llm = MagicMock()
    response = MagicMock()
    response.content = "{}"
    llm.invoke.return_value = response
    return llm


@pytest.fixture
def mock_search_client() -> MagicMock:
    """A MagicMock that mimics a SearchClient."""
    client = MagicMock()
    client.search_jobs.return_value = []
    client.search_company_reviews.return_value = []
    return client
