from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DB_PATH: str = Field(default=":memory:")
    EXAMS_SVC_URL: str = Field(default=...)
    TT_SVC_URL: str = Field(default=...)


settings = Settings()
