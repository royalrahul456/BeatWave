from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    TELEGRAM_BOT_TOKEN: str = "demo_bot_token"
    API_BASE_URL: str = "http://localhost:8000/api/v1"
    MINI_APP_URL: str = "https://mighty-cars-flash.loca.lt"
    LOG_LEVEL: str = "INFO"


bot_settings = BotSettings()
