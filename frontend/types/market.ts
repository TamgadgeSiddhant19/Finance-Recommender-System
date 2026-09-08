export interface OHLCData {
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface MarketQuote {
  instrument_key: string;
  symbol: string;
  name?: string;
  ltp: number;
  previous_close: number;
  change: number;
  change_percent: number;
  ohlc?: OHLCData;
  volume: number;
  timestamp: string;
  source: string;
  is_market_open: boolean;
}

export interface MarketStatusResponse {
  exchange: string;
  status: "OPEN" | "CLOSED" | "PRE_OPEN" | "POST_CLOSE" | "OFFLINE";
  is_trading: boolean;
  message: string;
  timestamp: string;
}

export interface MarketQuotesBatchResponse {
  quotes: Record<string, MarketQuote>;
  market_status: MarketStatusResponse;
  source: string;
  retrieved_at: string;
}

export interface HistoricalCandle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  open_interest?: number;
}
