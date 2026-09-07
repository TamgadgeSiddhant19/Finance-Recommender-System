"use client";

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Cell,
} from "recharts";
import { formatINR } from "@/lib/utils";

interface Props {
  income: number;
  expenses: number;
  savingsCapacity: number;
}

export function MonthlyCashflowChart({ income, expenses, savingsCapacity }: Props) {
  const data = [
    { name: "Monthly Income", amount: income, color: "#0284c7" },
    { name: "Living Expenses", amount: expenses, color: "#f43f5e" },
    { name: "SIP Capacity", amount: savingsCapacity, color: "#10b981" },
  ];

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const d = payload[0].payload;
      return (
        <div className="rounded-lg bg-slate-900 border border-slate-700 p-2.5 shadow-xl">
          <p className="text-xs font-semibold text-slate-200">{d.name}</p>
          <p className="text-xs font-bold text-slate-100 mt-1">{formatINR(d.amount)}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full h-56">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 11 }} />
          <YAxis
            stroke="#64748b"
            tick={{ fontSize: 11 }}
            tickFormatter={(val) => `₹${val / 1000}k`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="amount" radius={[6, 6, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
