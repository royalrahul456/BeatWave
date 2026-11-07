import os
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_default_api_base_url() -> str:
    port = os.getenv("PORT", "8000")
    return os.getenv("API_BASE_URL", f"http://127.0.0.1:{port}/api/v1")


def get_default_mini_app_url() -> str:
    # Check explicitly defined MINI_APP_URL, then Render's automatic external URL, then localhost
    url = os.getenv("MINI_APP_URL") or os.getenv("RENDER_EXTERNAL_URL") or "http://localhost:3000"
    if url and not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    TELEGRAM_BOT_TOKEN: str = "demo_bot_token"
    BOT_USERNAME: str = "BeatWave_app"
    MINI_APP_SHORT_NAME: str = os.getenv("MINI_APP_SHORT_NAME", "beatwave")
    API_BASE_URL: str = get_default_api_base_url()
    MINI_APP_URL: str = get_default_mini_app_url()
    LOG_LEVEL: str = "INFO"


bot_settings = BotSettings()
