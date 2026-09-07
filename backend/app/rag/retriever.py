from typing import List, Optional
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.rag.embeddings import EmbeddingService
from app.rag.models import Document, DocumentChunk
from app.rag.schemas import RetrievedChunk


def _compute_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    a = np.array(vec1, dtype=np.float32)
    b = np.array(vec2, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


class VectorRetriever:
    """
    Semantic vector retrieval engine with cosine similarity and metadata filtering.
    """

    def __init__(
        self,
        db: AsyncSession,
        embedding_service: Optional[EmbeddingService] = None,
    ):
        self.db = db
        self.embedding_service = embedding_service or EmbeddingService.get_instance()

    async def retrieve(
        self,
        query: str,
        top_k: int = 4,
        topic: Optional[str] = None,
        asset_class: Optional[str] = None,
        organization: Optional[str] = None,
        document_type: Optional[str] = None,
        min_similarity: float = 0.0,
    ) -> List[RetrievedChunk]:
        """
        Execute semantic similarity search with optional metadata constraints.
        """
        query_vector = self.embedding_service.embed_text(query)

        # Query chunks with joined documents and applied SQL filters
        stmt = (
            select(DocumentChunk)
            .join(Document, DocumentChunk.document_id == Document.id)
            .options(selectinload(DocumentChunk.document))
        )

        if topic:
            stmt = stmt.where(Document.topic == topic.lower().strip())
        if asset_class:
            stmt = stmt.where(Document.asset_class == asset_class.lower().strip())
        if organization:
            stmt = stmt.where(Document.organization.ilike(f"%{organization.strip()}%"))
        if document_type:
            stmt = stmt.where(Document.document_type == document_type.lower().strip())

        result = await self.db.execute(stmt)
        chunks = result.scalars().all()

        scored_chunks = []
        for chunk in chunks:
            doc = chunk.document
            if not doc:
                continue

            sim = _compute_cosine_similarity(query_vector, chunk.embedding)
            if sim >= min_similarity:
                scored_chunks.append((chunk, doc, sim))

        # Sort descending by cosine similarity score
        scored_chunks.sort(key=lambda x: x[2], reverse=True)

        return [
            RetrievedChunk(
                chunk_id=c.id,
                document_id=d.id,
                document_title=d.title,
                organization=d.organization,
                topic=d.topic,
                asset_class=d.asset_class,
                source=d.source,
                content=c.content,
                similarity_score=round(sim, 4),
                metadata=c.metadata_json,
            )
            for c, d, sim in scored_chunks[:top_k]
        ]
