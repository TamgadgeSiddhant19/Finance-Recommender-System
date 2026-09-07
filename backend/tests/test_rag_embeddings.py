from app.rag.embeddings import EmbeddingService


def test_embedding_service_singleton_and_dimensions():
    service1 = EmbeddingService.get_instance()
    service2 = EmbeddingService.get_instance()
    assert service1 is service2

    embedding = service1.embed_text("National Pension System Tier 1 tax rules")
    assert isinstance(embedding, list)
    assert len(embedding) == 384
    # All floats
    assert all(isinstance(val, float) for val in embedding)


def test_batch_embeddings():
    service = EmbeddingService.get_instance()
    texts = [
        "Sovereign Gold Bonds interest rate is 2.50% p.a.",
        "SEBI Mutual Fund Large Cap categorization",
        "Section 80C ELSS 3-year lock-in",
    ]
    batch_embeddings = service.embed_batch(texts)
    assert len(batch_embeddings) == 3
    for emb in batch_embeddings:
        assert len(emb) == 384
