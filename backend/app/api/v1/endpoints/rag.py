from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.rag.schemas import (
    RAGIngestionSummary,
    RAGQueryRequest,
    RAGQueryResponse,
)
from app.rag.service import RAGService

router = APIRouter()


@router.post(
    "/rag/ingest",
    response_model=RAGIngestionSummary,
    summary="Ingest Indian financial knowledge documents into pgvector",
)
async def ingest_knowledge_base(
    custom_directory: Optional[str] = Query(None, description="Optional custom directory path"),
    db: AsyncSession = Depends(get_db),
) -> RAGIngestionSummary:
    """
    Scan, parse, chunk, embed, and index authentic Indian financial knowledge documents (PDF, TXT, HTML) into PostgreSQL using pgvector.
    """
    target_dir: Optional[Path] = None
    if custom_directory:
        target_dir = Path(custom_directory)
    else:
        # Resolve data/documents/ relative to backend or repo root
        candidates = [
            Path("../data/documents"),
            Path("data/documents"),
            Path("../../data/documents"),
        ]
        for c in candidates:
            if c.exists() and c.is_dir():
                target_dir = c
                break

    if target_dir is None or not target_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not find documents directory at 'data/documents/'.",
        )

    service = RAGService(db)
    return await service.ingest_directory(target_dir)


@router.post(
    "/rag/query",
    response_model=RAGQueryResponse,
    summary="Query financial knowledge using semantic vector search and RAG synthesis",
)
async def query_knowledge_base(
    request: RAGQueryRequest,
    db: AsyncSession = Depends(get_db),
) -> RAGQueryResponse:
    """
    Execute semantic similarity search using SentenceTransformers and pgvector,
    and return an explainable, regulatory-grounded answer with source citations.
    """
    service = RAGService(db)
    return await service.query_pipeline(request)
