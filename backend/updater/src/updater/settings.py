from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    CANTEEN_SVC_URL: str = Field(default=...)
    LECTURES_SVC_URL: str = Field(default=...)
    EXAMS_SVC_URL: str = Field(default=...)


settings = Settings()
