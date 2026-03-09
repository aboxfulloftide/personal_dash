from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "Personal Dash"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str
    WEATHER_DB_URL: str = ""  # Connection string for external weather database

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS - Allow all origins in development, specific origins in production
    # Set CORS_ORIGINS in .env as comma-separated list: "http://localhost:5173,http://192.168.1.100:5173"
    # Or set to ["*"] to allow all origins (development only!)
    CORS_ORIGINS: List[str] = ["*"]  # Allow all origins by default for easier development

    # JWT
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 28

    class Config:
        env_file = ".env"


settings = Settings()
