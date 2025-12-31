from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR.parent / ".env"


class Settings(BaseSettings):
    DOMAIN:str
    API_VER: str

    DATABASE_URL: str

    SECRET_KEY: str
    SALT: str

    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_SERVER: str
    MAIL_PORT: int
    MAIL_FROM: str

    REDIS_URL: str
    BROKER_URL: str
    BACKEND_URL: str

    class Config:
        env_file = ".env"

    model_config = SettingsConfigDict(env_file=ENV_PATH, extra="ignore")


Config = Settings()

#Celery config
broker_url = Config.BROKER_URL
backend_url = Config.BACKEND_URL

