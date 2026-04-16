from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    PROJECT_NAME: str = "OptimusApi"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_KEY: str = ""
    # Comma-separated origins allowed for CORS (browser direct calls).
    # Example: CORS_ORIGINS=https://cartum.azanolabs.com,https://app.example.com
    CORS_ORIGINS: str = ""

    def get_cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
