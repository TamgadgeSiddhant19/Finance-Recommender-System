import { apiClient } from "./api";
import { FinancialProduct } from "@/types";
import { MOCK_PRODUCTS } from "@/lib/mockData";

export const productsService = {
  async getProducts(params?: {
    asset_class?: string;
    product_type?: string;
    limit?: number;
    offset?: number;
  }): Promise<FinancialProduct[]> {
    try {
      const query = new URLSearchParams();
      if (params?.asset_class) query.append("asset_class", params.asset_class);
      if (params?.product_type) query.append("product_type", params.product_type);
      if (params?.limit) query.append("limit", params.limit.toString());
      if (params?.offset) query.append("offset", params.offset.toString());

      const url = `/financial-products?${query.toString()}`;
      const res = await apiClient<FinancialProduct[] | { items: FinancialProduct[]; total: number }>(url);
      
      if (Array.isArray(res)) {
        return res.length > 0 ? res : MOCK_PRODUCTS;
      }
      if (res && Array.isArray((res as any).items)) {
        return (res as any).items.length > 0 ? (res as any).items : MOCK_PRODUCTS;
      }
      return MOCK_PRODUCTS;
    } catch (err: any) {
      console.warn("Using sample products catalog (backend error or offline):", err.message);
      return MOCK_PRODUCTS;
    }
  },

  async ingestProducts(): Promise<{ status: string; products_ingested: number }> {
    return await apiClient<{ status: string; products_ingested: number }>(
      "/financial-products/ingest",
      { method: "POST" }
    );
  },
};
