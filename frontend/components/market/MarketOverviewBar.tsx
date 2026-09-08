"use client";

import React, { useEffect, useState } from "react";
import { TrendingUp, TrendingDown, Activity, Clock, RefreshCw } from "lucide-react";
import { marketService } from "@/services/marketService";
import { MarketQuotesBatchResponse } from "@/types/market";
import { formatINR, formatPercent } from "@/lib/utils";

export function MarketOverviewBar() {
  const [data, setData] = useState<MarketQuotesBatchResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());

  const fetchIndices = async () => {
    try {
      setIsLoading(true);
      const res = await marketService.getBenchmarkIndices();
      setData(res);
      setLastRefreshed(new Date());
    } catch (err) {
      console.warn("Failed to fetch Upstox benchmark quotes:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchIndices();
    // Poll market overview every 60 seconds
    const interval = setInterval(fetchIndices, 60000);
    return () => clearInterval(interval);
  }, []);

  if (!data && isLoading) {
    return (
      <div className="w-full bg-slate-900/90 border-b border-slate-800/80 px-4 py-2 flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-2">
          <Activity className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
          <span>Loading live Indian market data from Upstox...</span>
        </div>
      </div>
    );
  }

  const quotesList = data?.quotes ? Object.values(data.quotes) : [];
  const marketStatus = data?.market_status;
  const isMarketOpen = marketStatus?.is_trading ?? false;

  return (
    <div className="w-full bg-slate-950/80 backdrop-blur border-b border-slate-800/70 px-4 py-2">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3 text-xs">
        {/* Market Status & Source Attribution */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-slate-900 border border-slate-700/60">
            <span
              className={`w-2 h-2 rounded-full ${
                isMarketOpen
                  ? "bg-emerald-400 animate-pulse"
                  : "bg-slate-500"
              }`}
            />
            <span className="font-semibold text-[11px] text-slate-300">
              NSE: {marketStatus?.status || "MARKET"}
            </span>
          </div>

          <span className="text-[10px] text-slate-500 uppercase tracking-wider hidden sm:inline">
            Live Feed: <strong className="text-emerald-400 font-semibold">Upstox API v2</strong>
          </span>
        </div>

        {/* Index Quotes Ticker */}
        <div className="flex items-center gap-4 sm:gap-6 overflow-x-auto py-0.5 no-scrollbar">
          {quotesList.map((q) => {
            const isPositive = q.change >= 0;
            return (
              <div key={q.instrument_key} className="flex items-center gap-2 whitespace-nowrap">
                <span className="font-medium text-slate-300">{q.symbol}</span>
                <span className="font-semibold text-white">
                  {formatINR(q.ltp)}
                </span>
                <span
                  className={`flex items-center text-[11px] font-medium ${
                    isPositive ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {isPositive ? (
                    <TrendingUp className="w-3 h-3 mr-0.5 inline" />
                  ) : (
                    <TrendingDown className="w-3 h-3 mr-0.5 inline" />
                  )}
                  {isPositive ? "+" : ""}
                  {q.change.toFixed(2)} ({isPositive ? "+" : ""}
                  {formatPercent(q.change_percent)})
                </span>
              </div>
            );
          })}
        </div>

        {/* Refresh button & Timestamp */}
        <div className="hidden md:flex items-center gap-2 text-slate-500 text-[11px]">
          <Clock className="w-3 h-3" />
          <span>{lastRefreshed.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}</span>
          <button
            onClick={fetchIndices}
            disabled={isLoading}
            title="Refresh Quotes"
            className="p-1 hover:text-slate-300 rounded transition hover:bg-slate-800 disabled:opacity-50"
          >
            <RefreshCw className={`w-3 h-3 ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>
    </div>
  );
}
