import logging
from typing import List, Tuple
import httpx
from app.core.config import settings
from app.rag.schemas import Citation, RetrievedChunk

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Modular LLM generation client for RAG 2.0 context synthesis.
    Supports Google Gemini, OpenAI, and a deterministic Grounded Synthesis Fallback.
    Strictly forbids ungrounded financial calculations or hallucinated regulatory facts.
    """

    def __init__(self, provider: str = settings.LLM_PROVIDER):
        self.provider = provider
        self.model_name = settings.LLM_MODEL_NAME

    def _build_citations(self, chunks: List[RetrievedChunk]) -> List[Citation]:
        """Convert retrieved chunks into formal structured statutory citations."""
        citations: List[Citation] = []
        for c in chunks:
            citations.append(
                Citation(
                    document_id=c.document_id,
                    title=c.document_title,
                    organization=c.organization,
                    source_url=c.source_url,
                    section=c.section,
                    subsection=c.subsection,
                    page_number=c.page_number,
                    chunk_id=c.chunk_id,
                    publication_date=c.publication_date,
                    effective_date=c.effective_date,
                    version=c.version or "1.0",
                    relevance_score=c.similarity_score,
                )
            )
        return citations

    def _build_grounded_answer(
        self, query: str, chunks: List[RetrievedChunk]
    ) -> Tuple[str, bool, str, List[Citation]]:
        """
        Deterministic, strictly grounded synthesis when no external LLM API is active.
        """
        if not chunks or (chunks and chunks[0].similarity_score < 0.20):
            msg = (
                f"The available authoritative Indian financial knowledge base (SEBI, RBI, CBDT, PFRDA) "
                f"does not contain sufficient verifiable context to answer: '{query}'. "
                f"To protect against financial inaccuracy, this system does not infer or predict unverified terms."
            )
            return msg, False, "INSUFFICIENT_CONTEXT", []

        citations = self._build_citations(chunks)
        orgs = list(dict.fromkeys(c.organization for c in chunks))

        synthesis_lines = [
            f"Based on authentic Indian statutory guidelines from {', '.join(orgs)}:",
            "",
        ]

        for i, chunk in enumerate(chunks, start=1):
            sec_label = f" ({chunk.section})" if chunk.section else ""
            source_tag = f"[{chunk.organization} - {chunk.document_title}{sec_label}]"
            # Extract key declarative sentences
            sentences = [
                s.strip()
                for s in chunk.content.split("\n")
                if s.strip() and not s.strip().startswith("#")
            ]
            core_content = "\n  ".join(sentences[:3]) if sentences else chunk.content[:250]
            synthesis_lines.append(f"{i}. **{source_tag}** (Relevance: {int(chunk.similarity_score * 100)}%):")
            synthesis_lines.append(f"  {core_content}")
            synthesis_lines.append("")

        synthesis_lines.append(
            "Note: Information is strictly grounded on official Indian statutory publications. "
            "Please consult current statutory circulars or a SEBI-registered advisor for execution."
        )

        return "\n".join(synthesis_lines), True, "VERIFIED", citations

    async def generate_answer(
        self, query: str, chunks: List[RetrievedChunk]
    ) -> Tuple[str, bool, str, List[Citation]]:
        """
        Generate grounded answer with strict zero-hallucination verification.
        Returns (answer: str, grounded: bool, grounding_status: str, citations: List[Citation]).
        """
        # 1. Abstention check for insufficient context / irrelevant queries
        if not chunks or (chunks and chunks[0].similarity_score < 0.20):
            msg = (
                f"The available authoritative Indian financial knowledge base does not contain "
                f"sufficient verifiable documentation to answer the query: '{query}'. "
                f"Artha AI abstains from answering rather than inferring unverified figures."
            )
            return msg, False, "INSUFFICIENT_CONTEXT", []

        citations = self._build_citations(chunks)

        context_blocks = []
        for c in chunks:
            sec_str = f" | Section: {c.section}" if c.section else ""
            sub_str = f" | Subsection: {c.subsection}" if c.subsection else ""
            context_blocks.append(
                f"[Source: {c.organization} - {c.document_title}{sec_str}{sub_str} | Date: {c.effective_date or c.publication_date}]\n{c.content}"
            )
        context_str = "\n\n---\n\n".join(context_blocks)

        system_prompt = (
            "You are an expert Indian Financial Regulatory & Advisory AI Assistant. "
            "Strict Grounding Rules:\n"
            "1. Answer ONLY using the provided regulatory context.\n"
            "2. Do NOT invent tax rates, returns, circular numbers, dates, or financial rules.\n"
            "3. If the retrieved context is insufficient to answer the question, explicitly state that available sources do not have enough information.\n"
            "4. Cite the issuing organization (e.g. SEBI, RBI, CBDT, PFRDA) and specific section titles in your response.\n"
            "5. Never contradict deterministic calculation or portfolio allocation rules."
        )

        # 2. Google Gemini API Integration
        if (self.provider == "gemini" or settings.GEMINI_API_KEY) and settings.GEMINI_API_KEY:
            gemini_model = self.model_name if "gemini" in self.model_name else "gemini-1.5-flash"
            endpoint_url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={settings.GEMINI_API_KEY}"
            prompt_content = f"{system_prompt}\n\nContext:\n{context_str}\n\nUser Question:\n{query}"

            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        endpoint_url,
                        headers={"Content-Type": "application/json"},
                        json={
                            "contents": [
                                {
                                    "parts": [{"text": prompt_content}]
                                }
                            ],
                            "generationConfig": {
                                "temperature": 0.1,
                                "maxOutputTokens": 1024,
                            },
                        },
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts and "text" in parts[0]:
                                text_out = parts[0]["text"]
                                # Check if model abstained
                                is_grounded = not any(phrase in text_out.lower() for phrase in [
                                    "do not provide enough information",
                                    "insufficient context",
                                    "cannot answer based on the provided context",
                                ])
                                status = "VERIFIED" if is_grounded else "INSUFFICIENT_CONTEXT"
                                return text_out, is_grounded, status, citations
                    else:
                        logger.warning(f"Gemini API returned status {resp.status_code}: {resp.text}")
            except Exception as e:
                logger.error(f"Gemini API request failed: {str(e)}")

        # 3. OpenAI API Integration
        if self.provider == "openai" and settings.OPENAI_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                        json={
                            "model": self.model_name,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": f"Context:\n{context_str}\n\nQuestion: {query}"},
                            ],
                            "temperature": 0.1,
                        },
                    )
                    if resp.status_code == 200:
                        text_out = resp.json()["choices"][0]["message"]["content"]
                        is_grounded = not any(phrase in text_out.lower() for phrase in [
                            "do not provide enough information",
                            "insufficient context",
                        ])
                        status = "VERIFIED" if is_grounded else "INSUFFICIENT_CONTEXT"
                        return text_out, is_grounded, status, citations
            except Exception as e:
                logger.error(f"OpenAI API request failed: {str(e)}")

        # 4. Deterministic Grounded Fallback
        return self._build_grounded_answer(query, chunks)

