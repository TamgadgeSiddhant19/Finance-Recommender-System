"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { TrendingUp, ShieldCheck, Sparkles, Menu, X, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useFinancialData } from "@/hooks/useFinancialData";

export function Navbar() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { isBackendConnected } = useFinancialData();

  const isAppRoute = pathname !== "/";

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-600 shadow-md shadow-emerald-950 text-white font-bold text-lg">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="text-base font-bold tracking-tight text-white">Artha<span className="text-emerald-400">AI</span></span>
              <span className="hidden sm:inline-block ml-1.5 text-[10px] font-semibold text-slate-400 border border-slate-700/60 px-1.5 py-0.5 rounded">
                INDIA • INR ₹
              </span>
            </div>
          </Link>

          {!isAppRoute && (
            <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-300">
              <Link href="#features" className="hover:text-emerald-400 transition-colors">Features</Link>
              <Link href="#how-it-works" className="hover:text-emerald-400 transition-colors">How It Works</Link>
              <Link href="#security" className="hover:text-emerald-400 transition-colors">Security & Ethics</Link>
            </nav>
          )}
        </div>

        <div className="flex items-center gap-3">
          <Badge variant={isBackendConnected ? "emerald" : "slate"} size="sm" className="hidden sm:inline-flex">
            <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${isBackendConnected ? "bg-emerald-400 animate-pulse" : "bg-slate-400"}`} />
            {isBackendConnected ? "Engine Connected" : "Local Demo"}
          </Badge>

          {isAppRoute ? (
            <Link href="/advisor">
              <Button size="sm" variant="outline" className="border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/10 gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                AI Assistant
              </Button>
            </Link>
          ) : (
            <Link href="/dashboard">
              <Button size="sm" variant="primary" className="gap-1.5">
                Launch Platform
                <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            </Link>
          )}

          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden text-slate-400 hover:text-slate-100 p-1.5"
            aria-label="Toggle Navigation"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-slate-800 bg-slate-900/95 px-4 py-4 space-y-3">
          <Link
            href="/"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-sm font-medium text-slate-200 py-1"
          >
            Home
          </Link>
          <Link
            href="/dashboard"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-sm font-medium text-emerald-400 py-1"
          >
            Dashboard
          </Link>
          <Link
            href="/profile"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-sm font-medium text-slate-200 py-1"
          >
            Financial Profile
          </Link>
          <Link
            href="/advisor"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-sm font-medium text-slate-200 py-1"
          >
            AI Financial Advisor
          </Link>
        </div>
      )}
    </header>
  );
}
