import { apiClient } from "./api";
import { RAGQueryRequest, RAGQueryResponse } from "@/types";
import { MOCK_RAG_RESPONSE } from "@/lib/mockData";

export const ragService = {
  async queryKnowledge(request: RAGQueryRequest): Promise<RAGQueryResponse> {
    try {
      return await apiClient<RAGQueryResponse>("/rag/query", {
        method: "POST",
        body: JSON.stringify(request),
      });
    } catch (err: any) {
      console.warn("RAG query failed against backend, using grounded mock response:", err.message);
      return {
        ...MOCK_RAG_RESPONSE,
        query: request.query,
      };
    }
  },

  async ingestDocuments(): Promise<{ status: string; total_chunks_created: number }> {
    return await apiClient<{ status: string; total_chunks_created: number }>(
      "/rag/ingest",
      { method: "POST" }
    );
  },
};
