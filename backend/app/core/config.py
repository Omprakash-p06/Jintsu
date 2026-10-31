from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    BRAVE_API_KEY: str = ""
    META_API_KEY: str = ""
    META_API_BASE_URL: str = "https://api.meta.ai/v1"
    META_MODEL: str = "muse-spark-1.3"
    DATABASE_PATH: str = "data/jintru.db"
    REQUEST_DEADLINE_SECONDS: float = 8.0
    BRAVE_RETRIEVAL_MODE: Literal["snippets", "context"] = "snippets"
    USE_MOCK_PROVIDERS: bool = False


settings = Settings()
