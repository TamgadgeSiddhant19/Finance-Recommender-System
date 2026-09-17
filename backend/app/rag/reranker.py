import math
import re
from typing import List, Optional
from app.rag.schemas import RetrievedChunk


class Reranker:
    """
    RAG 2.0 Modular Reranking Engine.
    Refines hybrid candidate pools (top 20-30) into the top-K most authoritative,
    semantically aligned, section-relevant, and fresh statutory chunks.
    """

    def __init__(
        self,
        phrase_bonus_weight: float = 0.20,
        section_alignment_weight: float = 0.15,
        authority_weight: float = 0.10,
        freshness_weight: float = 0.05,
    ):
        self.phrase_bonus_weight = phrase_bonus_weight
        self.section_alignment_weight = section_alignment_weight
        self.authority_weight = authority_weight
        self.freshness_weight = freshness_weight

    def _extract_query_phrases(self, query: str) -> List[str]:
        """Extract multi-word continuous n-grams from user query."""
        tokens = [t.lower() for t in re.findall(r"\w+", query) if len(t) > 2]
        phrases = []
        if len(tokens) >= 2:
            for i in range(len(tokens) - 1):
                phrases.append(f"{tokens[i]} {tokens[i+1]}")
        return phrases

    def _calculate_freshness_bonus(self, effective_date: Optional[str], publication_date: Optional[str]) -> float:
        """
        Calculate date recency bonus (e.g., 2024 regulations score higher than older ones).
        """
        date_str = effective_date or publication_date or ""
        year_match = re.search(r"20(1\d|2\d)", date_str)
        if year_match:
            try:
                year = int("20" + year_match.group(1))
                if year >= 2024:
                    return 1.0
                elif year == 2023:
                    return 0.8
                elif year >= 2020:
                    return 0.5
                else:
                    return 0.2
            except ValueError:
                pass
        return 0.5

    def rerank(
        self,
        query: str,
        candidates: List[RetrievedChunk],
        top_k: int = 4,
    ) -> List[RetrievedChunk]:
        """
        Rerank hybrid retrieval candidate pool into top-K grounded chunks.
        """
        if not candidates:
            return []

        query_lower = query.lower()
        query_terms = [t for t in re.findall(r"\w+", query_lower) if len(t) > 2]
        phrases = self._extract_query_phrases(query)

        reranked_chunks: List[RetrievedChunk] = []

        for chunk in candidates:
            content_lower = chunk.content.lower()
            section_lower = (chunk.section or "").lower()
            subsec_lower = (chunk.subsection or "").lower()
            title_lower = chunk.document_title.lower()
            full_context = f"{title_lower} {section_lower} {subsec_lower} {content_lower}"

            # 1. Base Score from Hybrid Retrieval
            chunk_hybrid = getattr(chunk, "hybrid_score", None)
            base_score = chunk_hybrid if chunk_hybrid is not None else chunk.similarity_score

            # 2. Phrase Match Bonus
            phrase_score = 0.0
            if phrases:
                matched_phrases = sum(1 for p in phrases if p in full_context)
                phrase_score = matched_phrases / len(phrases)

            # 3. Section / Subsection Alignment Bonus
            section_score = 0.0
            if chunk.section or chunk.subsection:
                matched_sec_terms = sum(1 for t in query_terms if t in section_lower or t in subsec_lower)
                if query_terms:
                    section_score = min(1.0, matched_sec_terms / max(1, len(query_terms)))

            # 4. Authoritative Regulatory Authority Match (e.g. SEBI in query -> SEBI document)
            authority_score = 0.5
            org_lower = chunk.organization.lower()
            if org_lower in query_lower:
                authority_score = 1.0

            # 5. Freshness Score
            freshness_score = self._calculate_freshness_bonus(chunk.effective_date, chunk.publication_date)

            # Composite Rerank Score
            rerank_score = (
                (0.50 * base_score)
                + (self.phrase_bonus_weight * phrase_score)
                + (self.section_alignment_weight * section_score)
                + (self.authority_weight * authority_score)
                + (self.freshness_weight * freshness_score)
            )

            # Clamp between 0.0 and 1.0
            final_score = float(min(1.0, max(0.0, rerank_score)))

            updated_chunk = chunk.model_copy(
                update={
                    "similarity_score": round(final_score, 4),
                    "rerank_score": round(final_score, 4),
                }
            )
            reranked_chunks.append(updated_chunk)

        # Sort descending by final rerank score
        reranked_chunks.sort(key=lambda x: x.similarity_score, reverse=True)

        return reranked_chunks[:top_k]
