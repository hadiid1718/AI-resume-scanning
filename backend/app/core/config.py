from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = Field(default="AI Resume Scanning System", alias="APP_NAME")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    database_url: str = Field(
        default="postgresql+psycopg://resume_user:resume_password@localhost:5432/resume_scanner",
        alias="DATABASE_URL",
    )
    cors_origins: str = Field(default="http://localhost:8501", alias="CORS_ORIGINS")
    streamlit_backend_url: str = Field(default="http://localhost:8000", alias="STREAMLIT_BACKEND_URL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    upload_dir: str = Field(default="uploads", alias="UPLOAD_DIR")
    report_dir: str = Field(default="reports", alias="REPORT_DIR")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
