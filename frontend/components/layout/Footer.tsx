import React from "react";
import Link from "next/link";
import { ShieldCheck, Lock, ExternalLink } from "lucide-react";

export function Footer() {
  return (
    <footer className="w-full border-t border-slate-200 dark:border-slate-800/80 bg-slate-50 dark:bg-slate-950/90 text-slate-600 dark:text-slate-400 text-xs py-10 px-4 sm:px-6 lg:px-8 transition-colors">
      <div className="max-w-7xl mx-auto space-y-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="space-y-3 md:col-span-2">
            <div className="flex items-center gap-2">
              <div className="flex h-6 w-6 items-center justify-center rounded bg-emerald-600 text-white font-bold text-xs">
                ₹
              </div>
              <span className="text-sm font-bold text-slate-900 dark:text-slate-200">ArthaAI Financial Platform</span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed max-w-md">
              AI-powered, regulatory-grounded personal finance and investment recommendation engine designed specifically for Indian retail investors, salaried professionals, and families.
            </p>
            <div className="flex items-center gap-4 text-[11px] text-slate-500 dark:text-slate-400 pt-2">
              <span className="flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" /> SEBI-Aligned Bounds
              </span>
              <span className="flex items-center gap-1">
                <Lock className="w-3.5 h-3.5 text-sky-600 dark:text-sky-400" /> Private &amp; Secure
              </span>
            </div>
          </div>

          <div>
            <p className="text-xs font-semibold text-slate-900 dark:text-slate-200 uppercase tracking-wider mb-3">
              Platform Modules
            </p>
            <ul className="space-y-2 text-slate-600 dark:text-slate-400">
              <li><Link href="/dashboard" className="hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">Overview Dashboard</Link></li>
              <li><Link href="/profile" className="hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">Financial Profile</Link></li>
              <li><Link href="/risk" className="hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">Risk Assessment</Link></li>
              <li><Link href="/portfolio" className="hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">Portfolio Matrix</Link></li>
              <li><Link href="/advisor" className="hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">RAG AI Advisor</Link></li>
            </ul>
          </div>

          <div>
            <p className="text-xs font-semibold text-slate-900 dark:text-slate-200 uppercase tracking-wider mb-3">
              Regulatory References
            </p>
            <ul className="space-y-2 text-[11px]">
              <li className="flex items-center gap-1 text-slate-600 dark:text-slate-400">SEBI Mutual Fund Rules <ExternalLink className="w-2.5 h-2.5" /></li>
              <li className="flex items-center gap-1 text-slate-600 dark:text-slate-400">RBI Master Directions <ExternalLink className="w-2.5 h-2.5" /></li>
              <li className="flex items-center gap-1 text-slate-600 dark:text-slate-400">CBDT Finance Act 2024 <ExternalLink className="w-2.5 h-2.5" /></li>
              <li className="flex items-center gap-1 text-slate-600 dark:text-slate-400">PFRDA NPS Regulations <ExternalLink className="w-2.5 h-2.5" /></li>
            </ul>
          </div>
        </div>

        <div className="pt-6 border-t border-slate-200 dark:border-slate-800/60 flex flex-col md:flex-row items-center justify-between gap-4 text-[11px] text-slate-500 dark:text-slate-400">
          <p>© 2026 ArthaAI India. All calculations are mathematical models for educational and planning purposes.</p>
          <p className="text-amber-700 dark:text-amber-400/90 font-medium">Mutual fund investments are subject to market risks. Read all scheme documents carefully.</p>
        </div>
      </div>
    </footer>
  );
}
