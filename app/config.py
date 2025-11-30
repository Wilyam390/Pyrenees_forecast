from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"
    WEATHER_CACHE_TTL: int = 3600
    WEATHER_API_TIMEOUT: int = 30
    MAX_CONCURRENT_WEATHER_REQUESTS: int = 10
    WEATHER_API_URL: str = "https://api.open-meteo.com/v1/forecast"
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
