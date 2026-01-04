from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    vision_provider: str = "openai"
    text_provider: str = "anthropic"
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    vision_model: str = "gpt-4o"
    text_model: str = "claude-sonnet-4-5"
    review_model: str = "claude-opus-4-5"

    openai_base_url: str = "https://api.openai.com/v1"
    anthropic_base_url: str = "https://api.anthropic.com/v1"

    # API Server Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

    # Processing Configuration
    max_photos: int = 20
    max_review_cycles: int = 2
    max_reruns_per_agent: int = 1
    max_total_llm_calls: int = 12

    # Business Defaults
    default_margin_target: float = 0.33
    default_currency: str = "USD"

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/ins_sup_agent"

    # JobNimbus Integration
    jobnimbus_api_key: str = ""

    # Logging
    log_level: str = "INFO"

    @property
    def is_production(self) -> bool:
        return bool(self.openai_api_key or self.anthropic_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
