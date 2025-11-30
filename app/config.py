from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"
    WEATHER_CACHE_TTL: int = 3600
    DEBUG: bool = False

    class Config:
        env_file = ".env"

settings = Settings()