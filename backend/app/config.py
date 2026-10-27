"""Application settings, read from environment variables and an optional ``.env`` file."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]

DEFAULT_SECRET = "dev-only-secret-change-me"
DEFAULT_DEMO_PASSWORD = "campus@123"

# Cosine-similarity floor for the best retrieved passage, below which a question is treated
# as having no relevant source. Absolute similarity scales differ between embedding models,
# so these are starting points. Run `python -m app.cli.calibrate` after changing the model.
_MIN_SCORE_BY_MODEL_HINT: tuple[tuple[str, float], ...] = (
    ("hash", 0.12),
    ("e5", 0.74),
    ("bge", 0.40),
)
_MIN_SCORE_FALLBACK = 0.35


def _split_csv(value: object) -> object:
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    app_name: str = "LPU Campus Assistant"
    environment: Literal["development", "production", "test"] = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api"
    timezone: str = "Asia/Kolkata"
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    enabled_assistants: Annotated[list[str], NoDecode] = ["university", "placement"]
    trust_forwarded_for: bool = False

    # Security
    secret_key: SecretStr = SecretStr(DEFAULT_SECRET)
    access_token_expire_minutes: int = 480
    bcrypt_rounds: int = 12
    demo_password: SecretStr = SecretStr(DEFAULT_DEMO_PASSWORD)
    chat_rate_limit_per_minute: int = 20
    login_rate_limit_per_minute: int = 10

    # Storage
    database_url: str = f"sqlite:///{BACKEND_DIR / 'var' / 'campus.db'}"
    vector_dir: Path = BACKEND_DIR / "var" / "chroma"
    docs_dir: Path = BACKEND_DIR / "data" / "docs"
    config_dir: Path = BACKEND_DIR / "data" / "config"
    seed_dir: Path = BACKEND_DIR / "data" / "seed"
    static_dir: Path = BACKEND_DIR / "app" / "static"
    auto_seed: bool = True
    auto_ingest: bool = True

    # Retrieval
    embedding_provider: Literal["sentence-transformers", "hash"] = "sentence-transformers"
    embedding_model: str = "intfloat/multilingual-e5-small"
    embedding_device: str | None = None
    vector_store: Literal["chroma", "memory"] = "chroma"
    chunk_size: int = 900
    chunk_overlap: int = 120
    retrieval_top_k: int = 5
    retrieval_candidates: int = 20
    min_retrieval_score: float | None = None
    require_citations: bool = True

    # Language model (any OpenAI-compatible chat completions endpoint)
    llm_base_url: str | None = None
    llm_api_key: SecretStr | None = None
    llm_model: str | None = None
    llm_timeout_seconds: float = 30.0
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1024
    llm_reasoning_effort: str | None = None

    # Placement policy (kept in sync with the placement policy document)
    placement_offer_multiplier: float = 1.5

    @field_validator("cors_origins", "enabled_assistants", mode="before")
    @classmethod
    def _parse_csv(cls, value: object) -> object:
        return _split_csv(value)

    @field_validator(
        "llm_base_url",
        "llm_model",
        "llm_reasoning_effort",
        "embedding_device",
        "min_retrieval_score",
        mode="before",
    )
    @classmethod
    def _blank_to_none(cls, value: object) -> object:
        return None if isinstance(value, str) and not value.strip() else value

    @property
    def llm_enabled(self) -> bool:
        return bool(self.llm_base_url and self.llm_model)

    @property
    def effective_min_retrieval_score(self) -> float:
        if self.min_retrieval_score is not None:
            return self.min_retrieval_score
        hint = "hash" if self.embedding_provider == "hash" else self.embedding_model.lower()
        for needle, score in _MIN_SCORE_BY_MODEL_HINT:
            if needle in hint:
                return score
        return _MIN_SCORE_FALLBACK

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    def insecure_defaults(self) -> list[str]:
        """Names of settings still at their development defaults (relevant in production)."""
        problems = []
        if self.secret_key.get_secret_value() == DEFAULT_SECRET:
            problems.append("SECRET_KEY")
        if self.demo_password.get_secret_value() == DEFAULT_DEMO_PASSWORD:
            problems.append("DEMO_PASSWORD")
        return problems


@lru_cache
def get_settings() -> Settings:
    return Settings()
