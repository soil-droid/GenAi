"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Typed application settings.

    All values are loaded from environment variables (or a .env file).
    """

    # GCP
    gcp_project_id: str = "your-gcp-project-id"
    gcp_region: str = "us-central1"
    gemini_model: str = "gemini-1.5-pro-preview-0409"

    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/productivity_db"

    # Application
    environment: str = "development"
    log_level: str = "INFO"
    cors_origins: list[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton – import this instance everywhere
settings = Settings()
