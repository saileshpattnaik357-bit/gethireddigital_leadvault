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

    # Harness: optional LLM second opinion on borderline classifications.
    # Off by default. Requires ANTHROPIC_API_KEY. See harness/llm.py.
    LEADVAULT_LLM_VALIDATION: str = "0"
    # Provider: ollama (local, free) | openai (Cloud Run) | anthropic
    LEADVAULT_LLM_PROVIDER: str = "ollama"
    # Model id for the chosen provider, e.g. mistral / qwen2.5:1.5b for ollama, gpt-4o-mini for openai
    LEADVAULT_LLM_MODEL: str = "mistral"
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    # Seconds per model call. Local models cold-start slowly; 60 is safe for ollama, 20 for cloud.
    LEADVAULT_LLM_TIMEOUT: int = 60


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
