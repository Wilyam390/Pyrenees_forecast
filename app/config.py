"""
Application configuration.
"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database URL - defaults to SQLite for local dev
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"
    
    # Weather API settings
    WEATHER_CACHE_TTL: int = 3600
    
    # Debug mode
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()