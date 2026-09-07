import { apiClient } from "./api";
import { FinancialProduct } from "@/types";
import { MOCK_PRODUCTS } from "@/lib/mockData";

export const productsService = {
  async getProducts(params?: {
    asset_class?: string;
    product_type?: string;
    limit?: number;
    offset?: number;
  }): Promise<{ items: FinancialProduct[]; total: number }> {
    try {
      const query = new URLSearchParams();
      if (params?.asset_class) query.append("asset_class", params.asset_class);
      if (params?.product_type) query.append("product_type", params.product_type);
      if (params?.limit) query.append("limit", params.limit.toString());
      if (params?.offset) query.append("offset", params.offset.toString());

      const url = `/financial-products?${query.toString()}`;
      return await apiClient<{ items: FinancialProduct[]; total: number }>(url);
    } catch (err: any) {
      console.warn("Using sample products catalog (backend error or offline):", err.message);
      return { items: MOCK_PRODUCTS, total: MOCK_PRODUCTS.length };
    }
  },

  async ingestProducts(): Promise<{ status: string; products_ingested: number }> {
    return await apiClient<{ status: string; products_ingested: number }>(
      "/financial-products/ingest",
      { method: "POST" }
    );
  },
};
