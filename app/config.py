from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"
    
    WEATHER_CACHE_TTL: int = 3600
    
    DEBUG: bool = False

    MAX_CONCURRENT_WEATHER_REQUESTS: int = 10

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()