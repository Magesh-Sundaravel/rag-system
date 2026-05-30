from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Config from env (RETRIEVE_ prefix). GROQ_API_KEY is never logged."""

    model_config = SettingsConfigDict(env_prefix="RETRIEVE_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://rag:rag@localhost:5432/rag"

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Shared embedder (must match embedding-service / the vector(1024) column).
    model_name: str = "BAAI/bge-large-en-v1.5"
    embed_dim: int = 1024

    top_k: int = 5
    rrf_k: int = 60


settings = Settings()
