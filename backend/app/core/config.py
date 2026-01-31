from pydantic_settings import BaseSettings
from typing import List
from pydantic import computed_field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Personal Dash"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DBMS: str
    USER_NAME: str
    PASSWORD: str
    HOST: str
    DATABASE_NAME: str
    PORT: int

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return f"{self.DBMS}://{self.USER_NAME}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DATABASE_NAME}"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    # JWT
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 28

    class Config:
        env_file = ".env"
        extra = 'ignore'

settings = Settings()
