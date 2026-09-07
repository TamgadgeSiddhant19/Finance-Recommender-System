export interface RetrievedChunk {
  chunk_id: number;
  document_id: number;
  document_title: string;
  organization: string;
  topic: string;
  asset_class: string;
  source: string;
  content: string;
  similarity_score: number;
  metadata: Record<string, any>;
}

export interface RAGQueryRequest {
  query: string;
  top_k?: number;
  topic?: string;
  asset_class?: string;
  organization?: string;
  document_type?: string;
  min_similarity?: number;
}

export interface RAGQueryResponse {
  query: string;
  answer: string;
  sources: RetrievedChunk[];
  total_retrieved: number;
  llm_provider: string;
  model_name: string;
}

export interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  content: string;
  sources?: RetrievedChunk[];
  timestamp: string;
  isLoading?: boolean;
}
