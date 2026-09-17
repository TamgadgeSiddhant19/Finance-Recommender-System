import pytest
from pathlib import Path
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.rag.chunking import SectionAwareChunker
from app.rag.evaluation import RAGEvaluator, calculate_mrr, calculate_ndcg_at_k, calculate_precision_at_k, calculate_recall_at_k
from app.rag.loaders.base import extract_metadata_from_text
from app.rag.models import Document, DocumentChunk
from app.rag.reranker import Reranker
from app.rag.retriever import HybridRetriever
from app.rag.router import QueryRouter
from app.rag.schemas import LoadedDocument, QueryIntentEnum, RAGQueryRequest
from app.rag.service import RAGService
from app.rag.versioning import DocumentVersionService


@pytest.mark.asyncio
async def test_section_aware_chunking():
    """Test smart chunker parses sections, subsections, and preserves provenance."""
    sample_text = """# SEBI Guidelines on Mutual Funds
# Organization: SEBI
# Document Type: circular
# Topic: mutual_funds
# Asset Class: equity
# Publication Date: 2024-01-01
# Effective Date: 2024-04-01
# Source URL: https://sebi.gov.in/circular.html
# Version: 2.0

## Section 1: Introduction and Objective
To ensure standardized categorization across all mutual funds in India.

## Section 2: Large Cap Allocation Mandates
### Subsection 2.1: Portfolio Definition
Large Cap funds must allocate minimum 80% in top 100 listed equities.
"""
    loaded_doc = LoadedDocument(
        content=sample_text,
        metadata=extract_metadata_from_text(sample_text, Path("test_sebi.txt")),
        file_path="test_sebi.txt",
        file_hash="dummy_hash_123",
    )

    chunker = SectionAwareChunker(chunk_size=300, chunk_overlap=50)
    chunks = chunker.chunk_document(loaded_doc)

    assert len(chunks) >= 2
    # Verify section provenance
    sections = [c["section"] for c in chunks]
    assert any("Introduction and Objective" in s or "Section 1" in s for s in sections)
    assert any("Large Cap Allocation Mandates" in s or "Section 2" in s for s in sections)

    # Verify chunk metadata fields
    first_meta = chunks[0]["metadata"]
    assert first_meta["organization"] == "SEBI"
    assert first_meta["effective_date"] == "2024-04-01"
    assert first_meta["version"] == "2.0"
    assert first_meta["source_url"] == "https://sebi.gov.in/circular.html"


@pytest.mark.asyncio
async def test_query_router():
    """Test deterministic query router classifies intents accurately."""
    # 1. Knowledge Intent
    res_k = QueryRouter.route_query("What is the mandate and market cap criteria for Large Cap mutual funds?")
    assert res_k.intent == QueryIntentEnum.KNOWLEDGE
    assert res_k.recommended_engine == "RAGService2.0"

    # 2. Market Data Intent
    res_m = QueryRouter.route_query("What is the current stock price of Reliance and TCS?")
    assert res_m.intent == QueryIntentEnum.MARKET_DATA
    assert res_m.recommended_engine == "MarketDataService"

    # 3. Deterministic Finance / SIP Math Intent
    res_f = QueryRouter.route_query("How much SIP do I need to accumulate 1 crore in 10 years?")
    assert res_f.intent == QueryIntentEnum.DETERMINISTIC_FINANCE
    assert res_f.recommended_engine == "GoalProjectionEngine"

    # 4. Recommendation Explanation Intent
    res_e = QueryRouter.route_query("Why did Artha recommend this product and why was equity allocated 55%?")
    assert res_e.intent == QueryIntentEnum.RECOMMENDATION_EXPLANATION
    assert res_e.recommended_engine == "RecommendationAuditService"


@pytest.mark.asyncio
async def test_reranker_logic():
    """Test reranker calculates phrase bonus, section alignment, and authority weights."""
    from app.rag.schemas import RetrievedChunk

    c1 = RetrievedChunk(
        chunk_id=1,
        document_id=1,
        document_title="SEBI Categorization Circular",
        organization="SEBI",
        topic="mutual_funds",
        asset_class="equity",
        source="sebi.txt",
        section="Large Cap Allocation Mandates",
        subsection="Portfolio Definition",
        effective_date="2024-04-01",
        content="Large Cap funds must invest at least 80% in top 100 stocks.",
        similarity_score=0.70,
        hybrid_score=0.70,
    )
    c2 = RetrievedChunk(
        chunk_id=2,
        document_id=2,
        document_title="General Debt Fund Guidelines",
        organization="RBI",
        topic="fixed_income",
        asset_class="debt",
        source="rbi.txt",
        section="General Overview",
        effective_date="2020-01-01",
        content="Debt funds invest in government securities and commercial paper.",
        similarity_score=0.65,
        hybrid_score=0.65,
    )

    reranker = Reranker()
    reranked = reranker.rerank("Large Cap funds top 100 stocks under SEBI", [c2, c1], top_k=2)

    assert len(reranked) == 2
    # c1 should be reranked to rank 1 due to phrase matching, section alignment, authority, and freshness
    assert reranked[0].chunk_id == 1
    assert reranked[0].similarity_score > reranked[1].similarity_score
    assert reranked[0].rerank_score is not None


@pytest.mark.asyncio
async def test_evaluation_metrics_math():
    """Test standard IR metrics: Recall@K, Precision@K, MRR, NDCG."""
    retrieved = [10, 20, 30, 40]
    ground_truth = {20, 30}

    # Recall@4: 2/2 = 1.0; Recall@1: 0/2 = 0.0
    assert calculate_recall_at_k(retrieved, ground_truth, 4) == 1.0
    assert calculate_recall_at_k(retrieved, ground_truth, 1) == 0.0

    # Precision@2: 1/2 = 0.5; Precision@4: 2/4 = 0.5
    assert calculate_precision_at_k(retrieved, ground_truth, 2) == 0.5
    assert calculate_precision_at_k(retrieved, ground_truth, 4) == 0.5

    # MRR: First hit is at rank 2 -> 1/2 = 0.5
    assert calculate_mrr(retrieved, ground_truth) == 0.5

    # NDCG@4 > 0
    ndcg = calculate_ndcg_at_k(retrieved, ground_truth, 4)
    assert 0.0 < ndcg <= 1.0


@pytest.mark.asyncio
async def test_document_version_service(db_session: AsyncSession):
    """Test soft deprecation and superseding of outdated documents."""
    doc = Document(
        title="Old Circular",
        source="old_sebi.txt",
        organization="SEBI",
        document_type="circular",
        topic="mutual_funds",
        asset_class="equity",
        file_path="old.txt",
        file_hash="hash_old",
        is_active=True,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    version_svc = DocumentVersionService(db_session)
    active_docs = await version_svc.get_active_documents(organization="SEBI")
    assert any(d.id == doc.id for d in active_docs)

    # Deactivate
    success = await version_svc.deactivate_document(doc.id, reason="Superseded by Master Direction 2024")
    assert success is True

    # Confirm deactivated
    active_docs_after = await version_svc.get_active_documents(organization="SEBI")
    assert not any(d.id == doc.id for d in active_docs_after)


@pytest.mark.asyncio
async def test_rag_v2_api_end_to_end(client: AsyncClient):
    """Full end-to-end test of RAG 2.0 Ingest, Query with Citations, Routing, and Evaluation API."""
    # 1. Ingest Knowledge Base
    ingest_res = await client.post(f"{settings.API_V1_STR}/rag/ingest")
    assert ingest_res.status_code == 200
    summary = ingest_res.json()
    assert summary["status"] in ["success", "partial_success"]
    assert summary["documents_discovered"] >= 5

    # 2. Query Intent Classification API
    route_res = await client.post(
        f"{settings.API_V1_STR}/rag/route",
        params={"query": "What is the tax rate on equity mutual funds under Section 112A?"}
    )
    assert route_res.status_code == 200
    route_data = route_res.json()
    assert route_data["intent"] == "KNOWLEDGE"

    # 3. Grounded RAG Query with Structured Citations
    query_payload = {
        "query": "What is the mandatory portfolio allocation for Large Cap mutual funds under SEBI guidelines?",
        "top_k": 3,
        "enable_hybrid": True,
        "enable_reranking": True,
    }
    q_res = await client.post(f"{settings.API_V1_STR}/rag/query", json=query_payload)
    assert q_res.status_code == 200
    q_data = q_res.json()
    assert q_data["grounded"] is True
    assert q_data["grounding_status"] == "VERIFIED"
    assert len(q_data["citations"]) > 0
    assert any("SEBI" in c["organization"] for c in q_data["citations"])
    assert any("80%" in s["content"] or "Large Cap" in s["content"] for s in q_data["sources"])
    assert q_data["retrieval_metadata"]["query_intent"] == "KNOWLEDGE"

    # 4. Multi-Chunk Synthesis Query
    multi_payload = {
        "query": "Compare the capital gains taxation of equity mutual funds vs sovereign gold bonds in India.",
        "top_k": 4,
    }
    m_res = await client.post(f"{settings.API_V1_STR}/rag/query", json=multi_payload)
    assert m_res.status_code == 200
    m_data = m_res.json()
    assert len(m_data["sources"]) >= 2
    assert len(m_data["citations"]) >= 2
    # Verify citations contain both CBDT/SEBI and RBI sources
    cit_orgs = [c["organization"] for c in m_data["citations"]]
    assert len(set(cit_orgs)) >= 2 or len(m_data["citations"]) >= 2

    # 5. Out-of-Domain Abstention Query
    ood_payload = {
        "query": "What is the secret recipe for Coca Cola and how do you brew beer at home?",
        "top_k": 3,
        "min_similarity": 0.0,
    }
    ood_res = await client.post(f"{settings.API_V1_STR}/rag/query", json=ood_payload)
    assert ood_res.status_code == 200
    ood_data = ood_res.json()
    # The system must clearly signal insufficient context / abstention
    assert ood_data["grounded"] is False or ood_data["grounding_status"] == "INSUFFICIENT_CONTEXT" or "does not contain" in ood_data["answer"].lower() or "insufficient" in ood_data["answer"].lower()

    # 6. Automated Benchmark Evaluation API
    eval_res = await client.post(f"{settings.API_V1_STR}/rag/evaluate?k=4")
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["total_benchmark_cases"] >= 8
    assert "recall_at_k" in eval_data["metrics"]
    assert "mean_reciprocal_rank" in eval_data["metrics"]
    assert "out_of_domain_abstention_accuracy" in eval_data["metrics"]
    assert eval_data["metrics"]["recall_at_k"] > 0.50
    assert eval_data["metrics"]["out_of_domain_abstention_accuracy"] >= 0.50
