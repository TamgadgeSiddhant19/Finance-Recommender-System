import logging
from typing import List
import httpx
from app.core.config import settings
from app.rag.schemas import RetrievedChunk

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Modular LLM generation client for RAG context synthesis.
    Supports Google Gemini, OpenAI, and a robust deterministic Grounded Synthesis Fallback.
    """

    def __init__(self, provider: str = settings.LLM_PROVIDER):
        self.provider = provider
        self.model_name = settings.LLM_MODEL_NAME

    def _build_grounded_answer(self, query: str, chunks: List[RetrievedChunk]) -> str:
        """
        Deterministic, grounded synthesis when no external LLM API keys are provided.
        Synthesizes factual knowledge directly from retrieved official regulatory context.
        """
        if not chunks:
            return (
                f"No specific regulatory or institutional documentation was found in the Indian financial "
                f"knowledge base matching the query: '{query}'. Please consider refining the query or filters."
            )

        # Build clean bulleted points with regulatory citations
        synthesis_lines = [
            f"Based on authentic Indian financial regulatory documentation from {', '.join(set(c.organization for c in chunks))}:",
            "",
        ]

        for i, chunk in enumerate(chunks, start=1):
            source_tag = f"[{chunk.organization} - {chunk.document_title}]"
            # Extract key declarative sentences
            sentences = [s.strip() for s in chunk.content.split("\n") if s.strip() and not s.strip().startswith("#")]
            core_content = "\n  ".join(sentences[:3]) if sentences else chunk.content[:200]
            synthesis_lines.append(f"{i}. **{source_tag}** (Relevance: {int(chunk.similarity_score * 100)}%):")
            synthesis_lines.append(f"  {core_content}")
            synthesis_lines.append("")

        synthesis_lines.append(
            "Note: This information is synthesized from official Indian financial rules (SEBI/RBI/CBDT/PFRDA). "
            "Please consult current statutory circulars or an authorized financial advisor for specific tax/investment execution."
        )

        return "\n".join(synthesis_lines)

    async def generate_answer(self, query: str, chunks: List[RetrievedChunk]) -> str:
        """
        Generate answer for query grounded on the retrieved chunks using Gemini, OpenAI, or Fallback.
        """
        context_str = "\n\n---\n\n".join(
            [f"Source: {c.organization} ({c.document_title})\n{c.content}" for c in chunks]
        )
        system_prompt = (
            "You are an expert Indian Financial Regulatory & Advisory AI Assistant. "
            "Answer the user's question accurately and concisely using ONLY the provided regulatory context. "
            "Cite the relevant organization (e.g. SEBI, RBI, CBDT, PFRDA) and guidelines. "
            "If the context does not contain the answer, state that clearly."
        )

        # 1. Google Gemini API Integration
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
                                "temperature": 0.2,
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
                                return parts[0]["text"]
                    else:
                        logger.warning(f"Gemini API returned status {resp.status_code}: {resp.text}")
            except Exception as e:
                logger.error(f"Gemini API request failed: {str(e)}")

        # 2. OpenAI API Integration
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
                            "temperature": 0.2,
                        },
                    )
                    if resp.status_code == 200:
                        return resp.json()["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"OpenAI API request failed: {str(e)}")

        # 3. Default Grounded Synthesis Fallback
        return self._build_grounded_answer(query, chunks)
