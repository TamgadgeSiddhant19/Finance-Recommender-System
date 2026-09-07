"use client";

import React from "react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { formatINR } from "@/lib/utils";

interface AllocationItem {
  asset_class: string;
  target_pct: number;
  monthly_sip_inr: number;
}

interface Props {
  data: AllocationItem[];
}

const COLORS: Record<string, string> = {
  equity: "#10b981", // Emerald
  debt: "#0284c7",   // Sky blue
  gold: "#f59e0b",   // Amber
  cash: "#64748b",   // Slate
};

const LABELS: Record<string, string> = {
  equity: "Equity (Stocks & Index MFs)",
  debt: "Debt (G-Sec & Bonds)",
  gold: "Gold (SGB & Gold ETFs)",
  cash: "Cash & High Yield FDs",
};

export function AllocationPieChart({ data }: Props) {
  const chartData = data.map((item) => ({
    name: LABELS[item.asset_class.toLowerCase()] || item.asset_class,
    rawKey: item.asset_class.toLowerCase(),
    value: item.target_pct,
    sip: item.monthly_sip_inr,
    color: COLORS[item.asset_class.toLowerCase()] || "#94a3b8",
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const d = payload[0].payload;
      return (
        <div className="rounded-lg bg-slate-900/95 border border-slate-700 p-3 shadow-xl backdrop-blur-md">
          <p className="text-xs font-semibold text-slate-200">{d.name}</p>
          <div className="mt-1 flex items-center justify-between gap-4 text-xs">
            <span className="text-slate-400">Target Weight:</span>
            <span className="font-medium text-emerald-400">{d.value}%</span>
          </div>
          <div className="flex items-center justify-between gap-4 text-xs">
            <span className="text-slate-400">Monthly SIP:</span>
            <span className="font-medium text-slate-100">{formatINR(d.sip)}</span>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full flex flex-col md:flex-row items-center justify-between gap-6">
      <div className="w-full h-64 md:w-1/2">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={65}
              outerRadius={95}
              paddingAngle={4}
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} stroke="rgba(15, 23, 42, 0.8)" strokeWidth={2} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="w-full md:w-1/2 flex flex-col gap-2.5">
        {chartData.map((item) => (
          <div
            key={item.name}
            className="flex items-center justify-between p-2.5 rounded-lg bg-slate-800/40 border border-slate-700/40"
          >
            <div className="flex items-center gap-2.5">
              <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: item.color }} />
              <span className="text-xs font-medium text-slate-300">{item.name}</span>
            </div>
            <div className="text-right">
              <span className="text-xs font-bold text-slate-100">{item.value}%</span>
              <span className="block text-[10px] text-slate-400">{formatINR(item.sip)}/mo</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
