from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Config from env (GATEWAY_ prefix). Shares JWT secret with auth-service to verify tokens."""

    model_config = SettingsConfigDict(env_prefix="GATEWAY_", env_file=".env", extra="ignore")

    auth_url: str = "http://auth-service:8000"
    ingestion_url: str = "http://ingestion-service:8000"
    retrieval_url: str = "http://retrieval-service:8000"

    jwt_secret: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"

    cors_origins: list[str] = ["*"]
    rate_limit: str = "100/minute"
    request_timeout_seconds: float = 60.0


settings = Settings()
