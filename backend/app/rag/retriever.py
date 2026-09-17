import math
import re
from typing import Dict, List, Optional, Tuple
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.rag.embeddings import EmbeddingService
from app.rag.models import Document, DocumentChunk
from app.rag.schemas import RetrievedChunk

# Common stop words to ignore during lexical keyword scoring
STOP_WORDS = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with",
    "by", "is", "are", "was", "were", "what", "which", "how", "does", "do", "can",
    "under", "from", "as", "into", "about", "who", "whom", "this", "that", "these",
}


def _compute_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    a = np.array(vec1, dtype=np.float32)
    b = np.array(vec2, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _compute_keyword_score(query: str, content: str, title: str = "", section: str = "") -> float:
    """
    Deterministic BM25-inspired lexical matching score between 0.0 and 1.0.
    Considers term frequencies in content, title, and section with phrase bonus.
    """
    cleaned_query = re.sub(r"[^\w\s]", " ", query.lower())
    query_tokens = [t for t in cleaned_query.split() if t not in STOP_WORDS and len(t) > 1]
    if not query_tokens:
        return 0.0

    text_target = f"{title} {section} {content}".lower()
    total_tokens = len(text_target.split())
    if total_tokens == 0:
        return 0.0

    matched_tokens = 0
    tf_sum = 0.0

    for token in set(query_tokens):
        # Term count
        count = text_target.count(token)
        if count > 0:
            matched_tokens += 1
            # Sub-linear term frequency saturation
            tf = math.log1p(count)
            # Bonus if token matches section heading or title
            if token in title.lower() or token in section.lower():
                tf *= 1.5
            tf_sum += tf

    coverage = matched_tokens / len(set(query_tokens))
    base_score = (tf_sum / (tf_sum + 2.0)) * 0.7 + (coverage * 0.3)

    # Exact phrase matching bonus (e.g. "large cap", "deposit insurance", "tier 1")
    if len(query_tokens) >= 2:
        bigrams = [" ".join(query_tokens[i:i+2]) for i in range(len(query_tokens)-1)]
        phrase_matches = sum(1 for bg in bigrams if bg in text_target)
        if phrase_matches > 0:
            base_score = min(1.0, base_score + 0.15 * (phrase_matches / len(bigrams)))

    return float(np.clip(base_score, 0.0, 1.0))


class HybridRetriever:
    """
    RAG 2.0 Hybrid Retrieval Engine.
    Combines dense semantic pgvector embeddings with lexical keyword matching,
    retrieving an enriched candidate pool for downstream reranking.
    """

    def __init__(
        self,
        db: AsyncSession,
        embedding_service: Optional[EmbeddingService] = None,
        vector_weight: float = 0.65,
        keyword_weight: float = 0.35,
    ):
        self.db = db
        self.embedding_service = embedding_service or EmbeddingService.get_instance()
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight

    async def retrieve(
        self,
        query: str,
        top_k: int = 4,
        candidate_pool_size: int = 25,
        topic: Optional[str] = None,
        asset_class: Optional[str] = None,
        organization: Optional[str] = None,
        document_type: Optional[str] = None,
        product_type: Optional[str] = None,
        min_similarity: float = 0.0,
        only_active: bool = True,
    ) -> List[RetrievedChunk]:
        """
        Execute hybrid similarity search with SQL metadata constraints.
        Returns a ranked list of candidate chunks with vector, keyword, and combined scores.
        """
        query_vector = self.embedding_service.embed_text(query)

        stmt = (
            select(DocumentChunk)
            .join(Document, DocumentChunk.document_id == Document.id)
            .options(selectinload(DocumentChunk.document))
        )

        if only_active:
            stmt = stmt.where(Document.is_active.is_(True))
        if topic:
            stmt = stmt.where(Document.topic == topic.lower().strip())
        if asset_class:
            stmt = stmt.where(Document.asset_class == asset_class.lower().strip())
        if organization:
            stmt = stmt.where(Document.organization.ilike(f"%{organization.strip()}%"))
        if document_type:
            stmt = stmt.where(Document.document_type == document_type.lower().strip())
        if product_type:
            stmt = stmt.where(Document.product_type == product_type.lower().strip())

        result = await self.db.execute(stmt)
        chunks = result.scalars().all()

        scored_candidates: List[RetrievedChunk] = []

        for chunk in chunks:
            doc = chunk.document
            if not doc:
                continue

            vec_sim = _compute_cosine_similarity(query_vector, chunk.embedding)
            kw_sim = _compute_keyword_score(
                query=query,
                content=chunk.content,
                title=doc.title,
                section=chunk.section or "",
            )

            # Combined hybrid weighted score
            hybrid_score = (self.vector_weight * vec_sim) + (self.keyword_weight * kw_sim)

            # Boost slightly for active canonical regulations and matching section titles
            if chunk.section and any(term in (chunk.section or "").lower() for term in query.lower().split() if len(term) > 3):
                hybrid_score = min(1.0, hybrid_score + 0.05)

            if hybrid_score >= min_similarity:
                scored_candidates.append(
                    RetrievedChunk(
                        chunk_id=chunk.id,
                        document_id=doc.id,
                        document_title=doc.title,
                        organization=doc.organization,
                        topic=doc.topic,
                        asset_class=doc.asset_class,
                        product_type=doc.product_type,
                        jurisdiction=doc.jurisdiction,
                        source=doc.source,
                        source_url=doc.source_url,
                        section=chunk.section,
                        subsection=chunk.subsection,
                        page_number=chunk.page_number,
                        publication_date=doc.publication_date,
                        effective_date=doc.effective_date,
                        version=doc.version,
                        is_active=doc.is_active,
                        content=chunk.content,
                        similarity_score=round(hybrid_score, 4),
                        vector_score=round(vec_sim, 4),
                        keyword_score=round(kw_sim, 4),
                        hybrid_score=round(hybrid_score, 4),
                        metadata=chunk.metadata_json,
                    )
                )

        # Sort descending by hybrid similarity score
        scored_candidates.sort(key=lambda x: x.similarity_score, reverse=True)

        return scored_candidates[:candidate_pool_size]


# Backward-compatible alias
VectorRetriever = HybridRetriever

