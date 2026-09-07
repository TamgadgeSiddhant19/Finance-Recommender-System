from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """
    Standardized domain metadata associated with a financial knowledge document.
    """
    title: str = Field(..., description="Document title or header")
    source: str = Field(..., description="File name, origin, or URL")
    organization: str = Field(..., description="Issuing body e.g. SEBI, RBI, CBDT, PFRDA, AMFI")
    document_type: str = Field(..., description="Category e.g. circular, guidelines, tax_code, faq")
    topic: str = Field(..., description="Financial topic e.g. mutual_funds, taxation, retirement")
    asset_class: str = Field(..., description="Target asset class e.g. equity, debt, gold, hybrid, all")
    publication_date: Optional[str] = Field(None, description="ISO date or publication timestamp string")


class LoadedDocument(BaseModel):
    """
    Parsed and cleaned document container from raw source files.
    """
    content: str
    metadata: DocumentMetadata
    file_path: str
    file_hash: str


class ChunkMetadata(BaseModel):
    """
    Enriched metadata attached to an individual text chunk.
    """
    source: str
    organization: str
    document_type: str
    topic: str
    asset_class: str
    publication_date: Optional[str] = None
    chunk_index: int
    char_count: int


class DocumentChunkCreate(BaseModel):
    """
    Schema for persisting a vector chunk in the database.
    """
    chunk_index: int
    content: str
    metadata_json: Dict[str, Any]
    embedding: List[float]


class RetrievedChunk(BaseModel):
    """
    Retrieved knowledge segment with calculated cosine similarity score.
    """
    chunk_id: int
    document_id: int
    document_title: str
    organization: str
    topic: str
    asset_class: str
    source: str
    content: str
    similarity_score: float = Field(..., description="Cosine similarity score between 0.0 and 1.0")
    metadata: Dict[str, Any]


class RAGQueryRequest(BaseModel):
    """
    Payload for querying the Indian financial knowledge RAG pipeline.
    """
    query: str = Field(..., min_length=3, max_length=1000, description="Natural language financial query")
    top_k: int = Field(4, ge=1, le=20, description="Number of relevant chunks to retrieve")
    topic: Optional[str] = Field(None, description="Optional topic filter (e.g. mutual_funds, taxation)")
    asset_class: Optional[str] = Field(None, description="Optional asset class filter (e.g. equity, debt)")
    organization: Optional[str] = Field(None, description="Optional regulatory organization filter (e.g. SEBI, RBI)")
    document_type: Optional[str] = Field(None, description="Optional document type filter")
    min_similarity: float = Field(0.0, ge=0.0, le=1.0, description="Minimum cosine similarity cutoff")


class RAGQueryResponse(BaseModel):
    """
    Explainable response from the RAG pipeline containing synthesized answer and citations.
    """
    query: str
    answer: str
    sources: List[RetrievedChunk]
    total_retrieved: int
    llm_provider: str
    model_name: str


class RAGIngestionSummary(BaseModel):
    """
    Summary report generated after document ingestion pipeline finishes.
    """
    status: str
    documents_discovered: int
    documents_ingested: int
    documents_skipped: int
    total_chunks_created: int
    errors: List[str]
