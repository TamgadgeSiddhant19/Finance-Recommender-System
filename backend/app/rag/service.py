import logging
from pathlib import Path
from typing import List, Optional, Set, Tuple, Union
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.rag.chunking import SectionAwareChunker
from app.rag.embeddings import EmbeddingService
from app.rag.llm import LLMClient
from app.rag.loaders.factory import LOADER_MAPPING, get_loader_for_file
from app.rag.models import Document, DocumentChunk
from app.rag.reranker import Reranker
from app.rag.retriever import HybridRetriever
from app.rag.router import QueryRouter
from app.rag.schemas import (
    Citation,
    RAGIngestionSummary,
    RAGQueryRequest,
    RAGQueryResponse,
    RetrievedChunk,
)

logger = logging.getLogger(__name__)


class RAGService:
    """
    RAG 2.0 Production Orchestration Service.
    Coordinates recursive document ingestion, section-aware smart chunking,
    hybrid retrieval (pgvector + lexical), candidate reranking, query routing,
    and strict zero-hallucination grounded LLM synthesis with citations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.chunker = SectionAwareChunker()
        self.embedding_service = EmbeddingService.get_instance()
        self.retriever = HybridRetriever(db, self.embedding_service)
        self.reranker = Reranker()
        self.llm_client = LLMClient()

    async def ingest_document(self, file_path: Path) -> Tuple[bool, int, str]:
        """
        Ingest a single authoritative document: parse, chunk, embed, and store idempotently.
        Returns (success: bool, chunks_created: int, message: str).
        """
        try:
            loader = get_loader_for_file(file_path)
            loaded_doc = loader.load(file_path)

            if not loaded_doc.content.strip():
                return False, 0, f"File '{file_path.name}' is empty."

            # Check existing document by source and file_hash
            stmt = select(Document).where(Document.source == loaded_doc.metadata.source)
            result = await self.db.execute(stmt)
            existing_doc = result.scalar_one_or_none()

            if existing_doc and existing_doc.file_hash == loaded_doc.file_hash:
                return True, 0, f"Document '{file_path.name}' unchanged (skipped)."

            # If document exists but hash changed, remove old record and its chunks
            if existing_doc:
                await self.db.delete(existing_doc)
                await self.db.flush()

            # 1. Section-aware chunking
            chunks_data = self.chunker.chunk_document(loaded_doc)
            if not chunks_data:
                return False, 0, f"No chunks generated for '{file_path.name}'."

            # 2. Embed chunks in batch
            texts_to_embed = [c["content"] for c in chunks_data]
            embeddings = self.embedding_service.embed_batch(texts_to_embed)

            # 3. Create Document ORM record with full authoritative metadata
            doc_record = Document(
                title=loaded_doc.metadata.title,
                source=loaded_doc.metadata.source,
                organization=loaded_doc.metadata.organization,
                document_type=loaded_doc.metadata.document_type,
                topic=loaded_doc.metadata.topic,
                asset_class=loaded_doc.metadata.asset_class,
                product_type=loaded_doc.metadata.product_type,
                jurisdiction=loaded_doc.metadata.jurisdiction,
                publication_date=loaded_doc.metadata.publication_date,
                effective_date=loaded_doc.metadata.effective_date,
                source_url=loaded_doc.metadata.source_url,
                version=loaded_doc.metadata.version,
                last_updated=loaded_doc.metadata.last_updated,
                is_active=loaded_doc.metadata.is_active,
                file_path=loaded_doc.file_path,
                file_hash=loaded_doc.file_hash,
                total_chunks=len(chunks_data),
            )
            self.db.add(doc_record)
            await self.db.flush()

            # 4. Create DocumentChunk records with section provenance
            for idx, c in enumerate(chunks_data):
                chunk_record = DocumentChunk(
                    document_id=doc_record.id,
                    chunk_index=c["chunk_index"],
                    section=c.get("section"),
                    subsection=c.get("subsection"),
                    page_number=c.get("page_number"),
                    paragraph_index=c.get("paragraph_index"),
                    content=c["content"],
                    metadata_json=c["metadata"],
                    embedding=embeddings[idx],
                )
                self.db.add(chunk_record)

            await self.db.commit()
            return True, len(chunks_data), f"Successfully ingested '{file_path.name}' ({len(chunks_data)} chunks)."

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error ingesting document '{file_path.name}': {str(e)}")
            return False, 0, f"Failed to ingest '{file_path.name}': {str(e)}"

    async def ingest_directory(self, directory_path: Union[str, Path]) -> RAGIngestionSummary:
        """
        Scan and recursively ingest all supported documents from a directory and subdirectories.
        """
        dir_path = Path(directory_path)
        if not dir_path.exists() or not dir_path.is_dir():
            return RAGIngestionSummary(
                status="error",
                documents_discovered=0,
                documents_ingested=0,
                documents_skipped=0,
                total_chunks_created=0,
                errors=[f"Directory does not exist: {dir_path}"],
            )

        # Recursive file discovery across subdirectories (sebi/, rbi/, cbdt/, etc.)
        supported_files: List[Path] = []
        seen_filenames: Set[str] = set()

        for p in dir_path.rglob("*"):
            if p.is_file() and p.suffix.lower() in LOADER_MAPPING:
                # Avoid duplicate files if both subfolder and root contain duplicate filename
                if p.name not in seen_filenames:
                    supported_files.append(p)
                    seen_filenames.add(p.name)

        discovered = len(supported_files)
        ingested = 0
        skipped = 0
        total_chunks = 0
        errors: List[str] = []

        for f in supported_files:
            success, chunks_created, msg = await self.ingest_document(f)
            if success:
                if chunks_created > 0:
                    ingested += 1
                    total_chunks += chunks_created
                else:
                    skipped += 1
            else:
                errors.append(msg)

        return RAGIngestionSummary(
            status="success" if not errors else "partial_success",
            documents_discovered=discovered,
            documents_ingested=ingested,
            documents_skipped=skipped,
            total_chunks_created=total_chunks,
            errors=errors,
        )

    async def query_pipeline(self, request: RAGQueryRequest) -> RAGQueryResponse:
        """
        Execute full RAG 2.0 Pipeline:
        Query -> Intent Classification -> Hybrid Retrieval -> Candidate Pool -> Reranker -> Grounded Synthesis -> Citations.
        """
        # 1. Deterministic Intent Classification
        route_res = QueryRouter.route_query(request.query)

        # 2. Hybrid Retrieval (Vector + Keyword) for Candidate Pool
        candidate_pool: List[RetrievedChunk] = await self.retriever.retrieve(
            query=request.query,
            top_k=request.top_k,
            candidate_pool_size=request.candidate_pool_size,
            topic=request.topic,
            asset_class=request.asset_class,
            organization=request.organization,
            document_type=request.document_type,
            product_type=request.product_type,
            min_similarity=request.min_similarity,
            only_active=True,
        )

        # 3. Candidate Pool Reranking
        if request.enable_reranking and candidate_pool:
            final_chunks = self.reranker.rerank(
                query=request.query,
                candidates=candidate_pool,
                top_k=request.top_k,
            )
        else:
            final_chunks = candidate_pool[:request.top_k]

        # 4. Strict Grounded Synthesis & Citations
        answer, is_grounded, grounding_status, citations = await self.llm_client.generate_answer(
            query=request.query,
            chunks=final_chunks,
        )

        retrieval_meta = {
            "query_intent": route_res.intent.value,
            "router_confidence": route_res.confidence,
            "candidate_pool_size": len(candidate_pool),
            "reranked_chunks_count": len(final_chunks),
            "top_similarity_score": final_chunks[0].similarity_score if final_chunks else 0.0,
        }

        return RAGQueryResponse(
            query=request.query,
            answer=answer,
            grounded=is_grounded,
            grounding_status=grounding_status,
            query_intent=route_res.intent.value,
            citations=citations,
            sources=final_chunks,
            total_retrieved=len(final_chunks),
            llm_provider=self.llm_client.provider,
            model_name=self.llm_client.model_name,
            retrieval_metadata=retrieval_meta,
        )

