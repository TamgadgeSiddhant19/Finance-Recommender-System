from pathlib import Path
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.rag.retriever import VectorRetriever
from app.rag.service import RAGService


@pytest.mark.asyncio
async def test_vector_retriever_and_metadata_filtering(db_session: AsyncSession, tmp_path: Path):
    # 1. Create 2 distinct sample financial knowledge documents
    doc1 = tmp_path / "gold_bonds.txt"
    doc1.write_text(
        "# Title: Sovereign Gold Bonds\n# Organization: RBI\n# Topic: gold_investments\n# Asset Class: gold\n\n"
        "Sovereign Gold Bonds offer a fixed 2.50% annual coupon and are completely exempt from capital gains tax upon maturity.",
        encoding="utf-8",
    )

    doc2 = tmp_path / "elss_tax.txt"
    doc2.write_text(
        "# Title: ELSS Mutual Funds\n# Organization: SEBI\n# Topic: mutual_funds\n# Asset Class: equity\n\n"
        "Equity Linked Savings Schemes (ELSS) have a mandatory 3-year lock-in period and qualify for Section 80C tax deduction.",
        encoding="utf-8",
    )

    service = RAGService(db_session)
    await service.ingest_document(doc1)
    await service.ingest_document(doc2)

    retriever = VectorRetriever(db_session)

    # 2. Query for Gold
    gold_results = await retriever.retrieve(query="What is the interest rate on Sovereign Gold Bonds?", top_k=2)
    assert len(gold_results) >= 1
    assert "Sovereign Gold Bonds" in gold_results[0].document_title
    assert gold_results[0].organization == "RBI"
    assert gold_results[0].similarity_score > 0.40

    # 3. Query with topic filter: mutual_funds
    mf_results = await retriever.retrieve(
        query="tax benefits on gold and mutual funds",
        topic="mutual_funds",
        top_k=2,
    )
    assert len(mf_results) == 1
    assert mf_results[0].topic == "mutual_funds"
    assert "ELSS" in mf_results[0].content

    # 4. Query with asset_class filter: gold
    gold_filtered = await retriever.retrieve(
        query="tax deductions",
        asset_class="gold",
        top_k=2,
    )
    assert len(gold_filtered) == 1
    assert gold_filtered[0].asset_class == "gold"
