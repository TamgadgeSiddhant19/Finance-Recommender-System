export interface Citation {
  document_id: number;
  title: string;
  organization: string;
  source_url?: string | null;
  section?: string | null;
  subsection?: string | null;
  page_number?: number | null;
  chunk_id: number;
  publication_date?: string | null;
  effective_date?: string | null;
  version: string;
  relevance_score: number;
}

export interface RetrievedChunk {
  chunk_id: number;
  document_id: number;
  document_title: string;
  organization: string;
  topic: string;
  asset_class: string;
  product_type?: string | null;
  jurisdiction?: string;
  source: string;
  source_url?: string | null;
  section?: string | null;
  subsection?: string | null;
  page_number?: number | null;
  publication_date?: string | null;
  effective_date?: string | null;
  version?: string;
  is_active?: boolean;
  content: string;
  similarity_score: number;
  vector_score?: number | null;
  keyword_score?: number | null;
  rerank_score?: number | null;
  metadata: Record<string, any>;
}

export interface RAGQueryRequest {
  query: string;
  top_k?: number;
  candidate_pool_size?: number;
  topic?: string;
  asset_class?: string;
  organization?: string;
  document_type?: string;
  product_type?: string;
  min_similarity?: number;
  enable_reranking?: boolean;
  enable_hybrid?: boolean;
}

export interface RAGQueryResponse {
  query: string;
  answer: string;
  grounded: boolean;
  grounding_status: "VERIFIED" | "INSUFFICIENT_CONTEXT" | "OUT_OF_DOMAIN" | "UNVERIFIED" | string;
  query_intent: "KNOWLEDGE" | "MARKET_DATA" | "DETERMINISTIC_FINANCE" | "RECOMMENDATION_EXPLANATION" | string;
  citations: Citation[];
  sources: RetrievedChunk[];
  total_retrieved: number;
  llm_provider: string;
  model_name: string;
  retrieval_metadata?: Record<string, any> | null;
}

export interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  content: string;
  grounded?: boolean;
  grounding_status?: string;
  query_intent?: string;
  citations?: Citation[];
  sources?: RetrievedChunk[];
  timestamp: string;
  isLoading?: boolean;
}

