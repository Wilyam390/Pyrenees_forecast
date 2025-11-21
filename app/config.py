"""
Application configuration management.
Supports environment-based configuration for dev/staging/prod.
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

env_path: Path = Path(__file__).resolve().parents[1] / '.env'
if env_path.exists():
    load_dotenv(env_path)


class Settings:
    """
    Application settings with environment variable support.
    
    All settings can be overridden via environment variables.
    Defaults are provided for local development.
    """
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite+aiosqlite:///./app.db"
    )
    
    # Weather API
    WEATHER_API_URL: str = os.getenv(
        "WEATHER_API_URL",
        "https://api.open-meteo.com/v1/forecast"
    )
    WEATHER_API_TIMEOUT: int = int(os.getenv("WEATHER_API_TIMEOUT", "20"))
    WEATHER_CACHE_TTL: int = int(os.getenv("WEATHER_CACHE_TTL", "3600"))
    MAX_CONCURRENT_WEATHER_REQUESTS: int = int(
        os.getenv("MAX_CONCURRENT_WEATHER_REQUESTS", "4")
    )
    
    APP_NAME: str = "Pyrenees Mountain Weather"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))


settings: Settings = Settings()