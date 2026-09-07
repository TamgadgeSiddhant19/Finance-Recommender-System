import pytest
from httpx import AsyncClient
from app.core.config import settings


@pytest.mark.asyncio
async def test_rag_api_ingest_and_query_end_to_end(client: AsyncClient):
    # 1. Ingest documents from data/documents/
    ingest_res1 = await client.post(f"{settings.API_V1_STR}/rag/ingest")
    assert ingest_res1.status_code == 200
    summary1 = ingest_res1.json()
    assert summary1["status"] in ["success", "partial_success"]
    assert summary1["documents_discovered"] >= 5
    assert summary1["documents_ingested"] >= 5
    assert summary1["total_chunks_created"] >= 5

    # 2. Ingestion Idempotency (Second Pass should skip unchanged documents)
    ingest_res2 = await client.post(f"{settings.API_V1_STR}/rag/ingest")
    assert ingest_res2.status_code == 200
    summary2 = ingest_res2.json()
    assert summary2["documents_ingested"] == 0
    assert summary2["documents_skipped"] >= 5

    # 3. Query RAG API: Mutual Fund Categorization
    query_payload = {
        "query": "What is the mandate and market cap criteria for Large Cap mutual funds under SEBI rules?",
        "top_k": 3,
        "topic": "mutual_funds",
    }
    query_res = await client.post(
        f"{settings.API_V1_STR}/rag/query",
        json=query_payload,
    )
    assert query_res.status_code == 200
    data = query_res.json()
    assert "answer" in data
    assert len(data["sources"]) > 0
    assert any("SEBI" in s["organization"] for s in data["sources"])
    assert any(s["similarity_score"] > 0.30 for s in data["sources"])
    assert any("80%" in s["content"] or "Large Cap" in s["content"] or "SEBI" in s["content"] for s in data["sources"])

    # 4. Query RAG API: Deposit Insurance (DICGC)
    query_dicgc = {
        "query": "How much deposit insurance does DICGC provide on bank fixed deposits in India?",
        "top_k": 2,
    }
    dicgc_res = await client.post(
        f"{settings.API_V1_STR}/rag/query",
        json=query_dicgc,
    )
    assert dicgc_res.status_code == 200
    dicgc_data = dicgc_res.json()
    assert len(dicgc_data["sources"]) > 0
    assert any("5,00,000" in s["content"] or "DICGC" in s["content"] for s in dicgc_data["sources"])
