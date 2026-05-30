from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Config from env (EMBED_ prefix)."""

    model_config = SettingsConfigDict(env_prefix="EMBED_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://rag:rag@localhost:5432/rag"
    aws_region: str = "us-east-1"
    sqs_queue_url: str = ""
    sqs_endpoint_url: str = ""

    # Must match the pgvector column: vector(1024). See repo CLAUDE.md.
    model_name: str = "BAAI/bge-large-en-v1.5"
    embed_dim: int = 1024

    poll_wait_seconds: int = 20
    poll_max_messages: int = 10


settings = Settings()
