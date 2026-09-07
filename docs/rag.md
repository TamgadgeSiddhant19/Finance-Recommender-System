# Financial Knowledge RAG Pipeline

The **Financial Knowledge RAG Pipeline** provides verified semantic retrieval and grounded natural language question-answering over official Indian financial regulations and institutional guidelines.

---

## 🏛️ Architecture & Knowledge Workflow

```
Official Regulatory Documents (SEBI, RBI, CBDT, PFRDA in data/documents/)
            ↓
Document Loaders (PDFLoader, HTMLLoader, TextLoader) + Text Cleaning
            ↓
DocumentChunker (Recursive Character Splitter + Metadata Preservation)
            ↓
EmbeddingService (SentenceTransformers all-MiniLM-L6-v2, 384-dim dense vectors)
            ↓
PostgreSQL Database (documents & document_chunks tables)
            ↓
VectorRetriever (Semantic Cosine Search + SQL Metadata Filters)
            ↓
Context Assembler (Grounding Context + Citations)
            ↓
LLM Synthesis Client (OpenAI / Gemini / Grounded Synthesis Fallback)
            ↓
Explainable Response (Answer + Source Citations + Relevance Scores)
```

---

## 🗄️ Database Schema

### 1. `documents` Table
Stores document-level provenance, regulatory metadata, and SHA-256 hashes for change detection.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `INTEGER` (PK) | Unique document ID |
| `title` | `VARCHAR(255)` | Document title or heading |
| `source` | `VARCHAR(255)` (Index) | Origin filename or reference identifier |
| `organization` | `VARCHAR(100)` (Index) | Issuing authority (`SEBI`, `RBI`, `CBDT`, `PFRDA`, `AMFI`) |
| `document_type` | `VARCHAR(50)` (Index) | Document category (`guidelines`, `circular`, `tax_code`, `faq`) |
| `topic` | `VARCHAR(50)` (Index) | Domain topic (`mutual_funds`, `fixed_income`, `taxation`, `retirement`, `gold_investments`) |
| `asset_class` | `VARCHAR(50)` (Index) | Asset class (`equity`, `debt`, `gold`, `cash`, `hybrid`, `all`) |
| `publication_date` | `VARCHAR(50)` | Date of circular or statutory amendment |
| `file_path` | `VARCHAR(500)` | Local filesystem path |
| `file_hash` | `VARCHAR(64)` (Index) | SHA-256 hash for idempotent ingestion |
| `total_chunks` | `INTEGER` | Total text chunks generated |
| `created_at` / `updated_at` | `TIMESTAMPTZ` | Record timestamps |

### 2. `document_chunks` Table
Stores text chunks alongside 384-dimensional vector embeddings and granular chunk metadata.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `INTEGER` (PK) | Unique chunk ID |
| `document_id` | `INTEGER` (FK CASCADE) | Parent document reference |
| `chunk_index` | `INTEGER` | 0-indexed position within parent document |
| `content` | `TEXT` | Segmented textual content |
| `metadata_json` | `JSON` | Complete copy of document and chunk metadata |
| `embedding` | `JSON / Vector(384)` | 384-dimensional dense semantic embedding vector |
| `created_at` | `TIMESTAMPTZ` | Creation timestamp |

---

## 🔍 Semantic Search & Vector Mathematics

1. **Embedding Generation**:
   The system utilizes `sentence-transformers/all-MiniLM-L6-v2`, mapping textual chunks to a 384-dimensional hypersphere where vectors are $L_2$-normalized ($||\vec{v}||_2 = 1$).
2. **Cosine Similarity**:
   For query vector $\vec{q}$ and chunk vector $\vec{c}$:
   $$\text{Cosine Similarity} = \frac{\vec{q} \cdot \vec{c}}{||\vec{q}|| \, ||\vec{c}||} = \sum_{i=1}^{384} q_i \cdot c_i$$
3. **Filtering**:
   Queries can combine semantic similarity with relational SQL filters (`topic`, `asset_class`, `organization`, `document_type`, `min_similarity`).

---

## 📡 API Endpoints

### 1. Ingest Knowledge Base
`POST /api/v1/rag/ingest`
- Ingests all `.txt`, `.html`, and `.pdf` files from `data/documents/`.
- Computes SHA-256 hashes to ensure **strict idempotency** (skips unchanged files).

### 2. Query Knowledge Base
`POST /api/v1/rag/query`

**Request Body**:
```json
{
  "query": "What is the LTCG tax rate on equity mutual funds in India?",
  "top_k": 3,
  "topic": "taxation",
  "asset_class": "equity"
}
```

**Response Body**:
```json
{
  "query": "What is the LTCG tax rate on equity mutual funds in India?",
  "answer": "Based on authentic Indian financial regulatory documentation from CBDT: ...",
  "sources": [
    {
      "chunk_id": 8,
      "document_id": 3,
      "document_title": "Taxation of Capital Gains on Investments in India",
      "organization": "CBDT",
      "topic": "taxation",
      "asset_class": "all",
      "source": "cbdt_capital_gains_taxation.txt",
      "content": "b) LTCG under Section 112A: Taxed at flat 12.5% on gains exceeding INR 1,25,000 per financial year.",
      "similarity_score": 0.8412,
      "metadata": { ... }
    }
  ],
  "total_retrieved": 1,
  "llm_provider": "mock",
  "model_name": "gpt-4o-mini"
}
```
