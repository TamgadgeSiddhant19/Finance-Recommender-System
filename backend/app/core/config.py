from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Core App Settings
    PROJECT_NAME: str = "AI Finance Recommendation System"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # CORS Configuration
    BACKEND_CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return []

    # Financial Localization Defaults
    DEFAULT_CURRENCY: str = "INR"
    TARGET_MARKET: str = "India"

    # Database Configuration (PostgreSQL)
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "admin"
    POSTGRES_DB: str = "finance_db"
    DATABASE_URL: str = ""

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Union[str, None], info) -> str:
        if isinstance(v, str) and v.strip():
            url = v.strip()
            # Convert standard postgres/postgresql URI schemes to asyncpg
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            # Normalize Neon / libpq query parameters for asyncpg
            if "sslmode=" in url:
                url = url.replace("sslmode=require", "ssl=require").replace("sslmode=verify-full", "ssl=require").replace("sslmode=prefer", "ssl=prefer")
            if "channel_binding=" in url:
                import re
                url = re.sub(r"&?channel_binding=[^&]+", "", url)
                url = url.replace("?&", "?").rstrip("?")
            return url

        values = info.data
        user = values.get("POSTGRES_USER", "postgres")
        password = values.get("POSTGRES_PASSWORD", "admin")
        server = values.get("POSTGRES_SERVER", "localhost")
        port = values.get("POSTGRES_PORT", 5432)
        db = values.get("POSTGRES_DB", "finance_db")
        return f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db}"

    # Phase 5: RAG & Knowledge Retrieval Settings
    RAG_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    RAG_EMBEDDING_DIM: int = 384
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 100
    RAG_DEFAULT_TOP_K: int = 4

    # Authentication & Security
    SECRET_KEY: str = "arthai_development_jwt_secret_key_change_in_production_987654321"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Market Data Provider Configuration ("demo" | "upstox" | "alphavantage")
    MARKET_DATA_PROVIDER: str = "demo"
    UPSTOX_ACCESS_TOKEN: Optional[str] = None
    UPSTOX_API_BASE_URL: str = "https://api.upstox.com/v2"
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    ALPHA_VANTAGE_BASE_URL: str = "https://www.alphavantage.co/query"

    # Modular LLM Configuration
    LLM_PROVIDER: str = "mock"  # "mock" | "openai" | "gemini" | "ollama"
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    LLM_MODEL_NAME: str = "gpt-4o-mini"


settings = Settings()

