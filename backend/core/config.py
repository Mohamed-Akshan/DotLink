from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


class Settings:
    """Read application configuration from the environment."""

    database_url = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/dotlink")
    secret_key = os.getenv("SECRET_KEY", "")
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    google_api_key = os.getenv("GOOGLE_API_KEY", "")
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    timezone = os.getenv("TIMEZONE", "Asia/Colombo")
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")


settings = Settings()
