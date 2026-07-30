from enum import StrEnum
from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Environment(StrEnum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    app_name: str = "SENTRY API"
    app_version: str = "0.1.0"
    environment: Environment = Environment.LOCAL
    log_level: str = "INFO"

    database_url: str = Field(
        default="postgresql+asyncpg://sentry:sentry_password@localhost:5432/sentry"
    )

    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["http://localhost:3000"])
    cors_allow_credentials: bool = True

    watsonx_api_key: str | None = Field(default=None)
    watsonx_project_id: str | None = Field(default=None)
    watsonx_url: str = Field(default="https://us-south.ml.cloud.ibm.com")
    # "granite-3-8b-instruct" isn't available on every watsonx.ai Runtime
    # instance/region - "granite-4-h-small" is confirmed available on the
    # team's project and is the current general-purpose Granite chat model.
    watsonx_model_id: str = Field(default="ibm/granite-4-h-small")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        # Managed Postgres providers (Render, Railway, Heroku, ...) hand out a
        # bare "postgresql://" URL, but create_async_engine needs the asyncpg
        # dialect prefix or it fails to find a compatible driver at startup.
        if value.startswith("postgresql://") or value.startswith("postgres://"):
            return "postgresql+asyncpg://" + value.split("://", 1)[1]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

