import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env from the backend directory
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    DATABASE_URL: str = "sqlite:///./price_tracker.db"
    SCRAPE_INTERVAL_MINUTES: int = 30
    FRONTEND_URL: str = "http://localhost:5173"

    # JWT Auth
    JWT_SECRET_KEY: str = "scrapo-secret-change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440  # 24 hours

    # Email (SMTP)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    NOTIFICATION_EMAIL: str = ""  # Default "from" address

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""  # Global fallback; per-user overrides in User model

    class Config:
        env_file = str(env_path)
        env_file_encoding = "utf-8"


settings = Settings()
