# Financial Knowledge RAG 2.0 Pipeline

The **Artha AI Financial Knowledge RAG 2.0 Pipeline** provides verified hybrid retrieval, section-aware smart chunking, candidate pool reranking, and strictly grounded natural language answers over authentic Indian financial statutory documents (SEBI, RBI, CBDT, PFRDA, AMFI, IRDAI).

---

## 🏛️ Architecture & Pipeline Flow

```
Official Regulatory Documents (SEBI, RBI, CBDT, PFRDA, AMFI, IRDAI in data/documents/*)
            ↓
Format Loaders (PDFLoader, HTMLLoader, TextLoader) + Metadata Extractor (Effective Dates, URLs, Version)
            ↓
SectionAwareChunker (Heading, Section, Subsection, Page Marker, and Sentence-Boundary Preservation)
            ↓
EmbeddingService (SentenceTransformers all-MiniLM-L6-v2, 384-dim normalized dense vectors)
            ↓
PostgreSQL Database (documents & document_chunks tables with full provenance metadata)
            ↓
User Financial Query → QueryRouter (Deterministic Intent: KNOWLEDGE | MARKET_DATA | FINANCE | EXPLANATION)
            ↓
HybridRetriever (Dense Cosine Similarity + BM25 Lexical Keyword Matching → Top 20-30 Candidates)
            ↓
Reranker (Phrase Matching + Section Alignment + Regulatory Authority + Freshness Scoring → Top K Chunks)
            ↓
Grounded LLM Client (Strict Gemini / OpenAI Grounding & Zero-Hallucination Fallback)
            ↓
Explainable Response (Answer + Grounded Status + Formal Statutory Citations + External Source URLs)
```

---

## ⚖️ Boundaries: What RAG Does vs Does NOT Do

| Domain Feature | Responsible Subsystem | RAG 2.0 Responsibility |
| :--- | :--- | :--- |
| Statutory Regulations & Definitions | **RAG 2.0** | Retrieves authentic circulars and explains rules |
| Tax Slabs & Exemption Limits | **RAG 2.0** | Synthesizes current Finance Act provisions with citations |
| Product Categorization Mandates | **RAG 2.0** | Explains SEBI portfolio caps (e.g., 80% Large Cap) |
| Numerical Goal SIP Math | **Deterministic Engines (Phase 7.1)** | **NOT** handled by RAG |
| Asset Allocation & Risk Scoring | **Deterministic Engines (Phase 7.2)** | **NOT** handled by RAG |
| Product Selection & Suitability | **Deterministic Engines (Phase 7.3)** | **NOT** handled by RAG |
| Live Tickers & Intraday Stock Quotes | **Market Data Foundation (Phase 6.5)** | Routed to `MarketDataService` |

---

## 🗄️ Database Schema & Provenance

### 1. `documents` Table
Stores authoritative metadata, statutory issuing body, validity period, and SHA-256 hashes for change detection.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `INTEGER` (PK) | Unique document ID |
| `title` | `VARCHAR(255)` | Official circular / guideline title |
| `source` | `VARCHAR(255)` (Index) | Origin filename |
| `organization` | `VARCHAR(100)` (Index) | Issuing authority (`SEBI`, `RBI`, `CBDT`, `PFRDA`, `AMFI`, `IRDAI`) |
| `document_type` | `VARCHAR(50)` (Index) | `circular`, `master_direction`, `guidelines`, `tax_code` |
| `topic` | `VARCHAR(50)` (Index) | Domain (`mutual_funds`, `fixed_income`, `taxation`, `retirement`, `insurance`) |
| `asset_class` | `VARCHAR(50)` (Index) | `equity`, `debt`, `gold`, `hybrid`, `all` |
| `product_type` | `VARCHAR(50)` | `mutual_fund`, `fixed_deposit`, `sgb`, `nps`, `life_insurance` |
| `jurisdiction` | `VARCHAR(20)` | Default `"IN"` (India) |
| `publication_date` | `VARCHAR(50)` | Date of circular release |
| `effective_date` | `VARCHAR(50)` | Applicable statutory enforcement date |
| `source_url` | `VARCHAR(500)` | Official government / regulatory portal link |
| `version` | `VARCHAR(20)` | Document version (e.g., `"2.1"`) |
| `is_active` | `BOOLEAN` (Index) | Active statutory enforcement flag |
| `file_hash` | `VARCHAR(64)` | SHA-256 hash for idempotent ingestion |
| `total_chunks` | `INTEGER` | Total text chunks generated |

### 2. `document_chunks` Table
Stores segmented clauses alongside 384-dimensional dense vector embeddings and hierarchical section provenance.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `INTEGER` (PK) | Unique chunk ID |
| `document_id` | `INTEGER` (FK CASCADE) | Parent document ID |
| `chunk_index` | `INTEGER` | 0-indexed position within document |
| `section` | `VARCHAR(255)` | Parsed statutory section (e.g. `Section 2: Equity Schemes`) |
| `subsection` | `VARCHAR(255)` | Parsed subsection (e.g. `Subsection 2.1: Large Cap`) |
| `page_number` | `INTEGER` | Page boundary where available |
| `paragraph_index` | `INTEGER` | Paragraph block sequence |
| `content` | `TEXT` | Segmented clause text |
| `metadata_json` | `JSON` | Complete copy of document provenance and metadata |
| `embedding` | `JSON / Vector(384)` | 384-dimensional dense semantic embedding vector |

---

## 🔍 Hybrid Retrieval & Candidate Reranking

1. **Dense Vector Search**:
   - Computes cosine similarity between user query embedding $\vec{q}$ and chunk vector $\vec{c}$:
     $$S_{vec}(\vec{q}, \vec{c}) = \frac{\vec{q} \cdot \vec{c}}{||\vec{q}|| \, ||\vec{c}||}$$
2. **Lexical BM25 Matching**:
   - Tokenizes query keywords and computes term frequency with sub-linear saturation and section heading bonuses:
     $$S_{kw}(q, c) = 0.7 \cdot \frac{\text{TF}}{1 + \text{TF}} + 0.3 \cdot \text{Coverage} + \text{PhraseBonus}$$
3. **Hybrid Score**:
   $$S_{hybrid} = 0.65 \cdot S_{vec} + 0.35 \cdot S_{kw}$$
4. **Candidate Pool & Reranker**:
   - Initial retrieval extracts top 20–30 candidates.
   - Secondary reranking pass scores candidate chunks based on:
     - Exact phrase matching ($w=0.20$)
     - Section title alignment ($w=0.15$)
     - Regulatory authority match ($w=0.10$)
     - Recency & effective date freshness ($w=0.05$)
   - Emits top $K$ (default 4) final grounded context segments.

---

## 🛡️ Strict Grounding & Abstention Behavior

- **Strict Prompt Engineering**: The LLM is instructed to synthesize answers strictly from the provided regulatory excerpts and cite specific sections.
- **Abstention & Zero-Hallucination**: If the retrieved candidate pool has similarity score $< 0.20$ or no relevant context is found, the engine abstains with `grounded = False` and `grounding_status = "INSUFFICIENT_CONTEXT"`.
- **Deterministic Grounded Fallback**: Operates reliably in test/offline environments without requiring external LLM API tokens.

---

## 📊 Benchmark Evaluation Framework

Located at `backend/app/rag/evaluation/`:
- **Metrics**:
  - `Recall@K`: Fraction of relevant statutory documents in top-K.
  - `Precision@K`: Proportion of top-K chunks that are relevant.
  - `MRR` (Mean Reciprocal Rank): Rank position of the first relevant chunk.
  - `NDCG@K`: Normalized Discounted Cumulative Gain accounting for rank positions.
  - `Out-of-Domain Abstention Accuracy`: Verification that ungrounded queries trigger abstention.
- **Benchmark API**: `POST /api/v1/rag/evaluate?k=4`

---

## 📡 API Endpoints

### 1. Recursive Document Ingestion
`POST /api/v1/rag/ingest`
- Recursively indexes documents in `data/documents/` subdirectories (`sebi/`, `rbi/`, `cbdt/`, `pfrda/`, `amfi/`, `irdai/`, `financial_education/`).
- Idempotent via SHA-256 hash checks.

### 2. Hybrid Grounded Query
`POST /api/v1/rag/query`

**Request Body**:
```json
{
  "query": "What are the capital gains tax rates on equity mutual funds under Finance Act 2024?",
  "top_k": 4,
  "enable_hybrid": true,
  "enable_reranking": true
}
```

**Response Body**:
```json
{
  "query": "What are the capital gains tax rates on equity mutual funds under Finance Act 2024?",
  "answer": "Under the Finance (No. 2) Act, 2024 (Section 112A & 111A)...",
  "grounded": true,
  "grounding_status": "VERIFIED",
  "query_intent": "KNOWLEDGE",
  "citations": [
    {
      "document_id": 3,
      "title": "CBDT Tax Circular: Capital Gains Taxation Framework under Finance Act 2024",
      "organization": "CBDT",
      "source_url": "https://incometaxindia.gov.in/communications/circular/circular-finance-act-2024.pdf",
      "section": "Section 2: Listed Equity & Equity-Oriented Mutual Funds",
      "subsection": "Subsection 2.3: Long-Term Capital Gains",
      "page_number": 1,
      "chunk_id": 8,
      "effective_date": "2024-07-23",
      "version": "1.0",
      "relevance_score": 0.94
    }
  ],
  "sources": [ ... ],
  "total_retrieved": 4,
  "llm_provider": "mock",
  "model_name": "gpt-4o-mini",
  "retrieval_metadata": {
    "query_intent": "KNOWLEDGE",
    "router_confidence": 0.90,
    "candidate_pool_size": 25,
    "reranked_chunks_count": 4,
    "top_similarity_score": 0.94
  }
}
```

### 3. Query Intent Routing
`POST /api/v1/rag/route?query=How+much+SIP+do+I+need`
- Returns detected intent (`KNOWLEDGE`, `MARKET_DATA`, `DETERMINISTIC_FINANCE`, `RECOMMENDATION_EXPLANATION`) with routing target.

### 4. Benchmark Evaluation
`POST /api/v1/rag/evaluate?k=4`
- Runs benchmark suite and outputs IR metrics.

