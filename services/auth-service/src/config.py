from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Config from env (AUTH_ prefix). Secrets are never hard-coded."""

    model_config = SettingsConfigDict(env_prefix="AUTH_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://rag:rag@localhost:5432/rag"
    jwt_secret: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 7


settings = Settings()
