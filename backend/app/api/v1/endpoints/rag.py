from pathlib import Path
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.rag.evaluation import RAGEvaluator
from app.rag.router import QueryRouter
from app.rag.schemas import (
    QueryRouteResult,
    RAGIngestionSummary,
    RAGQueryRequest,
    RAGQueryResponse,
)
from app.rag.service import RAGService

router = APIRouter()


@router.post(
    "/rag/ingest",
    response_model=RAGIngestionSummary,
    summary="Ingest authoritative Indian financial knowledge documents into pgvector",
)
async def ingest_knowledge_base(
    custom_directory: Optional[str] = Query(None, description="Optional custom directory path"),
    db: AsyncSession = Depends(get_db),
) -> RAGIngestionSummary:
    """
    Scan, parse, chunk, embed, and recursively index authentic Indian financial knowledge documents (PDF, TXT, HTML) into PostgreSQL using pgvector.
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
    summary="Query financial knowledge using RAG 2.0 hybrid search and grounded synthesis",
)
async def query_knowledge_base(
    request: RAGQueryRequest,
    db: AsyncSession = Depends(get_db),
) -> RAGQueryResponse:
    """
    Execute hybrid retrieval (pgvector + lexical matching) + candidate reranking,
    and return an explainable, regulatory-grounded answer with formal statutory citations.
    """
    service = RAGService(db)
    return await service.query_pipeline(request)


@router.post(
    "/rag/route",
    response_model=QueryRouteResult,
    summary="Deterministically classify user query intent",
)
async def route_query_intent(
    query: str = Query(..., min_length=2, description="Natural language prompt to classify"),
) -> QueryRouteResult:
    """
    Classify query into KNOWLEDGE, MARKET_DATA, DETERMINISTIC_FINANCE, or RECOMMENDATION_EXPLANATION.
    """
    return QueryRouter.route_query(query)


@router.post(
    "/rag/evaluate",
    summary="Execute automated RAG benchmark evaluation suite",
)
async def evaluate_rag_pipeline(
    k: int = Query(4, ge=1, le=10, description="Top-K retrieval cutoff"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Run benchmark evaluation computing Recall@K, Precision@K, MRR, NDCG, and Abstention accuracy.
    """
    evaluator = RAGEvaluator(db)
    return await evaluator.run_benchmark(k=k)

