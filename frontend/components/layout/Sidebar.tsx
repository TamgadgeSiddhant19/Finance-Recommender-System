"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  UserCheck,
  ShieldAlert,
  Target,
  PieChart,
  BotMessageSquare,
  Sparkles,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/profile", label: "Financial Profile", icon: UserCheck },
  { href: "/risk", label: "Risk Assessment", icon: ShieldAlert },
  { href: "/goals", label: "Goals", icon: Target },
  { href: "/portfolio", label: "Portfolio", icon: PieChart },
  { href: "/advisor", label: "AI Advisor", icon: BotMessageSquare, highlight: true },
  { href: "/recommendations", label: "Recommendations", icon: Sparkles },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden lg:flex w-64 flex-col shrink-0 border-r border-slate-200 dark:border-slate-800/80 bg-slate-50/70 dark:bg-slate-950/60 min-h-[calc(100vh-4rem)] p-4 transition-colors">
      <div className="space-y-1">
        <p className="px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">
          Management & Analytics
        </p>

        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150",
                isActive
                  ? "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30 font-semibold shadow-xs"
                  : "text-slate-600 dark:text-slate-300 hover:bg-slate-200/70 dark:hover:bg-slate-900 hover:text-slate-900 dark:hover:text-slate-100",
                item.highlight && !isActive && "text-sky-600 dark:text-sky-300 hover:text-sky-700 dark:hover:text-sky-200"
              )}
            >
              <Icon
                className={cn(
                  "w-4 h-4 shrink-0 transition-colors",
                  isActive ? "text-emerald-600 dark:text-emerald-400" : item.highlight ? "text-sky-600 dark:text-sky-400" : "text-slate-500 dark:text-slate-400"
                )}
              />
              <span className="flex-1">{item.label}</span>
              {item.highlight && (
                <span className="text-[10px] bg-sky-500/15 dark:bg-sky-500/20 text-sky-700 dark:text-sky-300 border border-sky-400/30 px-1.5 py-0.2 rounded font-semibold">
                  RAG
                </span>
              )}
            </Link>
          );
        })}
      </div>

      <div className="mt-auto space-y-3 pt-6 border-t border-slate-200 dark:border-slate-800/60">
        {/* Deterministic Engine Badge */}
        <div className="rounded-xl bg-gradient-to-br from-emerald-50 to-slate-100 dark:from-emerald-950/40 dark:to-slate-900 border border-emerald-200 dark:border-emerald-500/20 p-3.5">
          <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-400 text-xs font-semibold">
            <Zap className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            Deterministic Engine
          </div>
          <p className="text-[11px] text-slate-600 dark:text-slate-400 mt-1 leading-relaxed">
            Formulas strictly verified against SEBI investment rules & Indian compounding models.
          </p>
        </div>
      </div>
    </aside>
  );
}
