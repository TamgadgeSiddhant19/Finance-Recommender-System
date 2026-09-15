export interface OHLCData {
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface MarketQuote {
  symbol: string;
  instrument_id?: string;
  instrument_key?: string;
  exchange?: string;
  price?: number;
  ltp?: number;
  previous_close: number;
  change: number;
  change_percent: number;
  ohlc?: OHLCData;
  volume: number;
  timestamp: string;
  data_source: string;
  data_status: string;
  source?: string;
  is_market_open?: boolean;
}

export interface InstrumentInfo {
  symbol: string;
  name: string;
  exchange: string;
  instrument_type: string;
  provider_key: string;
  is_active: boolean;
  data_source: string;
}

export interface MarketStatusResponse {
  exchange: string;
  status: "OPEN" | "CLOSED" | "PRE_OPEN" | "POST_CLOSE" | "AFTER_HOURS" | "OFFLINE" | string;
  is_trading: boolean;
  message: string;
  timestamp: string;
  data_source?: string;
  data_status?: string;
}

export interface MarketQuotesBatchResponse {
  quotes: Record<string, MarketQuote>;
  market_status?: MarketStatusResponse;
  data_source?: string;
  data_status?: string;
  source?: string;
  timestamp?: string;
  retrieved_at?: string;
}

export interface HistoricalCandle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  open_interest?: number;
  data_source?: string;
  data_status?: string;
}
