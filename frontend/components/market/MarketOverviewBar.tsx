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
      <div className="w-full bg-slate-50 dark:bg-slate-900/90 border-b border-slate-200 dark:border-slate-800/80 px-4 py-2 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
        <div className="flex items-center gap-2">
          <Activity className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 animate-pulse" />
          <span>Loading live Indian market data from Upstox...</span>
        </div>
      </div>
    );
  }

  const quotesList = data?.quotes ? Object.values(data.quotes) : [];
  const marketStatus = data?.market_status;
  const isMarketOpen = marketStatus?.is_trading ?? false;

  return (
    <div className="w-full bg-slate-50/90 dark:bg-slate-950/80 backdrop-blur border-b border-slate-200 dark:border-slate-800/70 px-4 py-2 transition-colors">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3 text-xs">
        {/* Market Status & Source Attribution */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700/60 shadow-2xs">
            <span
              className={`w-2 h-2 rounded-full ${
                isMarketOpen
                  ? "bg-emerald-500 animate-pulse"
                  : "bg-slate-400"
              }`}
            />
            <span className="font-semibold text-[11px] text-slate-700 dark:text-slate-300">
              NSE: {marketStatus?.status || "MARKET"}
            </span>
          </div>

          <span className="text-[10px] text-slate-500 uppercase tracking-wider hidden sm:inline">
            Feed:{" "}
            <strong
              className={`font-semibold ${
                data?.data_source === "upstox"
                  ? "text-emerald-700 dark:text-emerald-400"
                  : "text-amber-700 dark:text-amber-400"
              }`}
            >
              {data?.data_source === "upstox"
                ? `Upstox API (${data?.data_status || "Live"})`
                : `Demo Feed (${data?.data_status || "Synthetic"})`}
            </strong>
          </span>
        </div>

        {/* Index Quotes Ticker */}
        <div className="flex items-center gap-4 sm:gap-6 overflow-x-auto py-0.5 no-scrollbar">
          {quotesList.map((q, idx) => {
            const numChange = Number(q.change ?? 0);
            const numChangePct = Number(q.change_percent ?? 0);
            const numLtp = Number(q.price ?? q.ltp ?? 0);
            const isPositive = numChange >= 0;
            const itemKey = q.symbol || q.instrument_id || q.instrument_key || `quote-${idx}`;

            return (
              <div key={itemKey} className="flex items-center gap-2 whitespace-nowrap">
                <span className="font-medium text-slate-600 dark:text-slate-300">{q.symbol}</span>
                <span className="font-semibold text-slate-900 dark:text-white">
                  {formatINR(numLtp)}
                </span>
                <span
                  className={`flex items-center text-[11px] font-semibold ${
                    isPositive ? "text-emerald-700 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"
                  }`}
                >
                  {isPositive ? (
                    <TrendingUp className="w-3 h-3 mr-0.5 inline" />
                  ) : (
                    <TrendingDown className="w-3 h-3 mr-0.5 inline" />
                  )}
                  {isPositive ? "+" : ""}
                  {numChange.toFixed(2)} ({isPositive ? "+" : ""}
                  {formatPercent(numChangePct)})
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
            className="p-1 hover:text-slate-800 dark:hover:text-slate-200 rounded transition hover:bg-slate-200 dark:hover:bg-slate-800 disabled:opacity-50 cursor-pointer"
          >
            <RefreshCw className={`w-3 h-3 ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>
    </div>
  );
}
