from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Config from env (INGEST_ prefix). AWS creds come from the standard chain."""

    model_config = SettingsConfigDict(env_prefix="INGEST_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://rag:rag@localhost:5432/rag"
    aws_region: str = "us-east-1"

    s3_bucket: str = "rag-raw-uploads"
    # Set to the LocalStack endpoint (http://localhost:4566) for local dev; empty in AWS.
    s3_endpoint_url: str = ""
    sqs_queue_url: str = ""
    sqs_endpoint_url: str = ""

    # Chunking knobs.
    fixed_chunk_tokens: int = 512
    fixed_chunk_overlap: int = 50
    recursive_chunk_chars: int = 1000
    sentence_chunk_chars: int = 1000


settings = Settings()
