from app.rag.chunking import DocumentChunker
from app.rag.schemas import DocumentMetadata, LoadedDocument


def test_chunker_sizes_overlap_and_metadata():
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)

    long_text = (
        "Section 1. Large Cap Mutual Funds in India must invest at least 80 percent of total assets in "
        "equity shares of the top 100 listed companies on the National Stock Exchange and Bombay Stock Exchange.\n\n"
        "Section 2. Mid Cap Mutual Funds in India must invest at least 65 percent of total assets in "
        "equity shares of companies ranked from 101 to 250 by full market capitalization.\n\n"
        "Section 3. Small Cap Mutual Funds in India must invest at least 65 percent of total assets in "
        "equity shares of companies ranked 251st and above by full market capitalization."
    )

    doc = LoadedDocument(
        content=long_text,
        metadata=DocumentMetadata(
            title="SEBI Categorization",
            source="sebi.txt",
            organization="SEBI",
            document_type="circular",
            topic="mutual_funds",
            asset_class="equity",
            publication_date="2024-01-01",
        ),
        file_path="/dummy/sebi.txt",
        file_hash="abcdef123456",
    )

    chunks = chunker.chunk_document(doc)
    assert len(chunks) >= 3

    for idx, c in enumerate(chunks):
        assert c["chunk_index"] == idx
        assert "content" in c and len(c["content"]) > 0
        meta = c["metadata"]
        assert meta["organization"] == "SEBI"
        assert meta["topic"] == "mutual_funds"
        assert meta["source"] == "sebi.txt"
        assert meta["chunk_index"] == idx
        assert meta["char_count"] == len(c["content"])
