from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_ENV: str = "development"
    APP_NAME: str = "BeatWave"
    APP_PUBLIC_URL: str = "http://localhost:3000"
    API_PUBLIC_URL: str = "http://localhost:8000"
    LOG_LEVEL: str = "INFO"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = "demo_bot_token"
    TELEGRAM_WEBHOOK_SECRET: str = ""
    TELEGRAM_WEBHOOK_URL: str = ""

    # Authentication / Sessions
    APP_SESSION_SECRET: str = "beatwave-super-secret-key-at-least-32-chars-long"
    TELEGRAM_INITDATA_MAX_AGE_SECONDS: int = 86400

    # Database & Cache
    DATABASE_URL: str = "sqlite+aiosqlite:///./beatwave.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    CORS_ALLOWED_ORIGINS: Union[str, List[str]] = ["*"]

    @field_validator("CORS_ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000", "http://localhost:5173"]

    # Security
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"

    # Music Provider
    MUSIC_PROVIDER: str = "demo"
    MUSIC_PROVIDER_API_KEY: str = ""
    MUSIC_PROVIDER_CLIENT_ID: str = ""
    MUSIC_PROVIDER_CLIENT_SECRET: str = ""

    # Rate Limiting
    REQUESTS_PER_USER_PER_WINDOW: int = 5
    REQUEST_RATE_LIMIT_WINDOW_SECONDS: int = 300


settings = Settings()
