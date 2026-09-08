import { apiClient } from "./api";
import { RAGQueryRequest, RAGQueryResponse } from "@/types";

export const ragService = {
  async queryKnowledge(request: RAGQueryRequest): Promise<RAGQueryResponse> {
    return await apiClient<RAGQueryResponse>("/rag/query", {
      method: "POST",
      body: JSON.stringify(request),
    });
  },

  async ingestDocuments(): Promise<{ status: string; total_chunks_created: number }> {
    return await apiClient<{ status: string; total_chunks_created: number }>(
      "/rag/ingest",
      { method: "POST" }
    );
  },
};
