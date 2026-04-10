from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import FrozenSet


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    # =========================
    # APP
    # =========================
    app_name: str
    env: str
    port: int
    api_version: str
    api_v1_prefix: str = "/api"

    # =========================
    # DATABASE
    # =========================
    database_url: str

    # =========================
    # REDIS
    # =========================
    redis_url: str

    # =========================
    # OLLAMA
    # =========================
    ollama_base_url: str
    ollama_model: str
    ollama_timeout: int

    # =========================
    # FILE UPLOAD
    # =========================
    upload_dir: str
    max_file_size: int

    allowed_image_mime_types: FrozenSet[str] = frozenset({
        "image/jpeg",
        "image/png",
        "image/webp",
    })

    # =========================
    # HASHING
    # =========================
    hamming_threshold: int

    # =========================
    # FRONTEND
    # =========================
    frontend_url: str


settings = Settings()
