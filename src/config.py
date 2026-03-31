"""Configuration management using pydantic-settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    openai_api_key: str = Field(default="", description="OpenAI API key")
    tavily_api_key: str = Field(default="", description="Tavily search API key")
    llm_model: str = Field(default="gpt-4o-mini", description="OpenAI model to use")
    max_job_results: int = Field(default=20, description="Maximum job results per search")
    max_shortlisted_jobs: int = Field(default=5, description="Maximum jobs to shortlist")
    output_dir: str = Field(default="./output", description="Directory for output files")

    def validate_openai_key(self) -> None:
        """Raise ValueError if OpenAI API key is not configured."""
        if not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set. "
                "Please copy .env.example to .env and add your OpenAI API key."
            )

    def validate_tavily_key(self) -> None:
        """Raise ValueError if Tavily API key is not configured."""
        if not self.tavily_api_key:
            raise ValueError(
                "TAVILY_API_KEY is not set. "
                "Please copy .env.example to .env and add your Tavily API key."
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()
