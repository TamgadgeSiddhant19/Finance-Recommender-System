from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QueryIntentEnum(str, Enum):
    """
    Deterministic Query Intent Classification taxonomy.
    """
    KNOWLEDGE = "KNOWLEDGE"
    MARKET_DATA = "MARKET_DATA"
    DETERMINISTIC_FINANCE = "DETERMINISTIC_FINANCE"
    RECOMMENDATION_EXPLANATION = "RECOMMENDATION_EXPLANATION"


class DocumentMetadata(BaseModel):
    """
    Standardized domain metadata associated with an authoritative financial knowledge document.
    """
    title: str = Field(..., description="Document title or header")
    source: str = Field(..., description="File name, origin, or URL")
    organization: str = Field(..., description="Issuing body e.g. SEBI, RBI, CBDT, PFRDA, AMFI, IRDAI")
    document_type: str = Field(..., description="Category e.g. circular, guidelines, tax_code, faq, regulation")
    topic: str = Field(..., description="Financial topic e.g. mutual_funds, taxation, retirement, fixed_income")
    asset_class: str = Field(..., description="Target asset class e.g. equity, debt, gold, hybrid, all")
    product_type: Optional[str] = Field(None, description="Specific product e.g. mutual_fund, sgb, fixed_deposit, nps")
    jurisdiction: str = Field("IN", description="Jurisdiction code, default IN (India)")
    publication_date: Optional[str] = Field(None, description="ISO date or publication timestamp string")
    effective_date: Optional[str] = Field(None, description="Applicable statutory effective date")
    source_url: Optional[str] = Field(None, description="Official authoritative URL")
    version: str = Field("1.0", description="Document regulatory version")
    last_updated: Optional[str] = Field(None, description="Timestamp of latest revision")
    is_active: bool = Field(True, description="Whether document is actively enforceable")


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
    Enriched metadata attached to an individual section/text chunk.
    """
    source: str
    organization: str
    document_type: str
    topic: str
    asset_class: str
    product_type: Optional[str] = None
    jurisdiction: str = "IN"
    publication_date: Optional[str] = None
    effective_date: Optional[str] = None
    source_url: Optional[str] = None
    version: str = "1.0"
    is_active: bool = True
    section: Optional[str] = None
    subsection: Optional[str] = None
    page_number: Optional[int] = None
    paragraph_index: Optional[int] = None
    chunk_index: int
    char_count: int


class DocumentChunkCreate(BaseModel):
    """
    Schema for persisting a vector chunk in the database.
    """
    chunk_index: int
    section: Optional[str] = None
    subsection: Optional[str] = None
    page_number: Optional[int] = None
    paragraph_index: Optional[int] = None
    content: str
    metadata_json: Dict[str, Any]
    embedding: List[float]


class RetrievedChunk(BaseModel):
    """
    Retrieved knowledge segment with hybrid scoring and provenance metadata.
    """
    chunk_id: int
    document_id: int
    document_title: str
    organization: str
    topic: str
    asset_class: str
    product_type: Optional[str] = None
    jurisdiction: str = "IN"
    source: str
    source_url: Optional[str] = None
    section: Optional[str] = None
    subsection: Optional[str] = None
    page_number: Optional[int] = None
    publication_date: Optional[str] = None
    effective_date: Optional[str] = None
    version: Optional[str] = "1.0"
    is_active: bool = True
    content: str
    similarity_score: float = Field(..., description="Final combined relevance score between 0.0 and 1.0")
    vector_score: Optional[float] = Field(None, description="Cosine similarity score")
    keyword_score: Optional[float] = Field(None, description="Lexical / BM25 matching score")
    hybrid_score: Optional[float] = Field(None, description="Combined hybrid retrieval score")
    rerank_score: Optional[float] = Field(None, description="Cross-encoder / heuristic rerank score")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Citation(BaseModel):
    """
    Formal citation structure for grounded RAG answers.
    """
    document_id: int
    title: str
    organization: str
    source_url: Optional[str] = None
    section: Optional[str] = None
    subsection: Optional[str] = None
    page_number: Optional[int] = None
    chunk_id: int
    publication_date: Optional[str] = None
    effective_date: Optional[str] = None
    version: str = "1.0"
    relevance_score: float


class RAGQueryRequest(BaseModel):
    """
    Payload for querying the Indian financial knowledge RAG 2.0 pipeline.
    """
    query: str = Field(..., min_length=3, max_length=1000, description="Natural language financial query")
    top_k: int = Field(4, ge=1, le=20, description="Number of final relevant chunks to return")
    candidate_pool_size: int = Field(25, ge=5, le=50, description="Initial hybrid candidate pool size")
    topic: Optional[str] = Field(None, description="Optional topic filter (e.g. mutual_funds, taxation)")
    asset_class: Optional[str] = Field(None, description="Optional asset class filter (e.g. equity, debt)")
    organization: Optional[str] = Field(None, description="Optional regulatory organization filter (e.g. SEBI, RBI)")
    document_type: Optional[str] = Field(None, description="Optional document type filter")
    product_type: Optional[str] = Field(None, description="Optional product type filter")
    min_similarity: float = Field(0.0, ge=0.0, le=1.0, description="Minimum similarity cutoff")
    enable_reranking: bool = Field(True, description="Enable secondary ranking pass")
    enable_hybrid: bool = Field(True, description="Combine vector and keyword search")


class RAGQueryResponse(BaseModel):
    """
    Explainable response from RAG 2.0 containing synthesized grounded answer, citations, and metadata.
    """
    query: str
    answer: str
    grounded: bool = Field(True, description="Whether answer is strictly supported by retrieved context")
    grounding_status: str = Field("VERIFIED", description="VERIFIED | INSUFFICIENT_CONTEXT | OUT_OF_DOMAIN | UNVERIFIED")
    query_intent: str = Field("KNOWLEDGE", description="Detected intent: KNOWLEDGE | MARKET_DATA | DETERMINISTIC_FINANCE | RECOMMENDATION_EXPLANATION")
    citations: List[Citation] = Field(default_factory=list, description="Authoritative statutory citations")
    sources: List[RetrievedChunk] = Field(default_factory=list, description="Retrieved chunk details")
    total_retrieved: int
    llm_provider: str
    model_name: str
    retrieval_metadata: Optional[Dict[str, Any]] = None


class RAGIngestionSummary(BaseModel):
    """
    Summary report generated after document ingestion pipeline finishes.
    """
    status: str
    documents_discovered: int
    documents_ingested: int
    documents_skipped: int
    total_chunks_created: int
    errors: List[str] = Field(default_factory=list)


class QueryRouteResult(BaseModel):
    """
    Result from deterministic query intent router.
    """
    query: str
    intent: QueryIntentEnum
    confidence: float
    recommended_engine: str
    reasoning: str
    routing_metadata: Dict[str, Any] = Field(default_factory=dict)

