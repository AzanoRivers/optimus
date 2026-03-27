from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    PROJECT_NAME: str = "OptimusApi"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False


settings = Settings()
