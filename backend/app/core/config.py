from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Entropia API"
    database_url: str = "sqlite:///./entropia.db"
    api_v1_prefix: str = "/api/v1"
    redis_url: str = "redis://localhost:6379/0"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2"
    ollama_timeout_seconds: float = 30.0

    windows_upload_dir: str = "uploads/windows"
    windows_max_upload_bytes: int = 10 * 1024 * 1024
    windows_allowed_image_mime_types: frozenset[str] = frozenset(
        {
            "image/jpeg",
            "image/png",
            "image/webp",
            "image/gif",
        }
    )


settings = Settings()
