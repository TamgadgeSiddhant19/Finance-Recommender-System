import { apiClient } from "./api";
import {
  MarketQuote,
  MarketStatusResponse,
  MarketQuotesBatchResponse,
  HistoricalCandle,
} from "@/types/market";

export const marketService = {
  /**
   * Retrieves live quotes for key benchmark indices (Nifty 50, Nifty Bank, India VIX)
   */
  async getBenchmarkIndices(): Promise<MarketQuotesBatchResponse> {
    return apiClient<MarketQuotesBatchResponse>("/market/indices");
  },

  /**
   * Retrieves quotes for specific Upstox instrument keys
   */
  async getQuotes(instruments: string[]): Promise<MarketQuotesBatchResponse> {
    const params = new URLSearchParams();
    instruments.forEach((inst) => params.append("instruments", inst));
    return apiClient<MarketQuotesBatchResponse>(`/market/quotes?${params.toString()}`);
  },

  /**
   * Retrieves real-time quote for a single instrument
   */
  async getQuote(instrumentKey: string): Promise<MarketQuote> {
    return apiClient<MarketQuote>(`/market/quote/${encodeURIComponent(instrumentKey)}`);
  },

  /**
   * Retrieves market operational status (OPEN, CLOSED, PRE_OPEN, etc.)
   */
  async getMarketStatus(): Promise<MarketStatusResponse> {
    return apiClient<MarketStatusResponse>("/market/status");
  },

  /**
   * Retrieves historical candles for an instrument
   */
  async getHistoricalCandles(
    instrumentKey: string,
    interval: string = "day",
    fromDate?: string,
    toDate?: string
  ): Promise<HistoricalCandle[]> {
    const params = new URLSearchParams({ interval });
    if (fromDate) params.append("from_date", fromDate);
    if (toDate) params.append("to_date", toDate);
    return apiClient<HistoricalCandle[]>(
      `/market/historical/${encodeURIComponent(instrumentKey)}?${params.toString()}`
    );
  },
};
