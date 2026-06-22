from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "LeadVault Agentic AI Engine"
    ENVIRONMENT: str = "dev"
    FRONTEND_URL: str = "http://localhost:3000"

    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    APIFY_API_TOKENS: str = ""
    APIFY_LINKEDIN_ACTORS: str = "supreme_coder/linkedin-post,harvestapi/linkedin-post-search,get-leads/linkedin-scraper"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
