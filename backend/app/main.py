from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.api.v1.api import api_router
from app.core.config import settings
from app.database.session import engine
from app.database.base import Base
import app.models  # Ensure all models are registered

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure all tables and columns exist on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Idempotent column migrations for existing tables
        await conn.execute(text("ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS goal_horizon_bucket VARCHAR(50);"))
        await conn.execute(text("ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS goal_feasibility_status VARCHAR(50);"))
        await conn.execute(text("ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS goal_metadata JSON;"))
        await conn.execute(text("ALTER TABLE recommendation_items ADD COLUMN IF NOT EXISTS intelligence_metadata JSON;"))
        # RAG 2.0 Document metadata columns
        await conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS product_type VARCHAR(50);"))
        await conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS jurisdiction VARCHAR(20) DEFAULT 'IN';"))
        await conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS effective_date VARCHAR(50);"))
        await conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS source_url VARCHAR(500);"))
        await conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS version VARCHAR(20) DEFAULT '1.0';"))
        await conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS last_updated VARCHAR(50);"))
        await conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;"))
        # RAG 2.0 DocumentChunk provenance columns
        await conn.execute(text("ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS section VARCHAR(255);"))
        await conn.execute(text("ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS subsection VARCHAR(255);"))
        await conn.execute(text("ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS page_number INTEGER;"))
        await conn.execute(text("ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS paragraph_index INTEGER;"))
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
    }
