"use client";

import React from "react";
import Link from "next/link";
import {
  TrendingUp,
  ShieldCheck,
  Cpu,
  Database,
  ArrowRight,
  CheckCircle2,
  Lock,
  LineChart,
  Layers,
  Sparkles,
  BookOpen,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Footer } from "@/components/layout/Footer";
import { MarketOverviewBar } from "@/components/market/MarketOverviewBar";

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Live Market Bar from Upstox */}
      <MarketOverviewBar />

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-16 pb-20 lg:pt-24 lg:pb-32 transition-colors">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-emerald-100/60 via-slate-50 to-white dark:from-emerald-950/30 dark:via-slate-950/70 dark:to-slate-950 -z-10" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/30 text-emerald-800 dark:text-emerald-400 text-xs font-semibold mb-6 shadow-2xs">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Built for the Indian Financial Market (INR ₹)</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-900 dark:text-white max-w-4xl mx-auto leading-tight">
            Deterministic Financial Logic Meets{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-600 via-teal-500 to-sky-600 dark:from-emerald-400 dark:via-teal-300 dark:to-sky-400">
              Regulatory RAG AI
            </span>
          </h1>

          <p className="mt-6 text-base sm:text-lg text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
            Stop relying on generic AI hallucinations for your money. Experience a unified wealth platform that calculates mathematical risk profiles and validates portfolio advice against official SEBI, RBI, and CBDT regulations.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/dashboard">
              <Button size="lg" className="w-full sm:w-auto text-base gap-2 px-6 bg-emerald-600 hover:bg-emerald-500 text-white shadow-md">
                Start Free Financial Assessment
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
            <Link href="/advisor">
              <Button size="lg" variant="outline" className="w-full sm:w-auto text-base gap-2 px-6 border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800">
                <BookOpen className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                Ask Regulatory AI Advisor
              </Button>
            </Link>
          </div>

          {/* Quick Metrics Bar */}
          <div className="mt-14 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 shadow-2xs dark:shadow-none">
              <p className="text-2xl font-bold text-emerald-700 dark:text-emerald-400">₹0 Hallucination</p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">100% Math-Verified Rules</p>
            </div>
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 shadow-2xs dark:shadow-none">
              <p className="text-2xl font-bold text-sky-700 dark:text-sky-400">384-Dim Vector</p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">SEBI &amp; RBI RAG Knowledge</p>
            </div>
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 shadow-2xs dark:shadow-none">
              <p className="text-2xl font-bold text-amber-800 dark:text-amber-400">Multi-Factor</p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Risk Scoring (0–100)</p>
            </div>
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 shadow-2xs dark:shadow-none">
              <p className="text-2xl font-bold text-purple-700 dark:text-purple-400">Finance Act 2024</p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Capital Gains Tax Rules</p>
            </div>
          </div>
        </div>
      </section>

      {/* Product Explanation / Core Architecture */}
      <section id="features" className="py-20 border-t border-slate-200 dark:border-slate-800/80 bg-slate-50/60 dark:bg-slate-900/40 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <Badge variant="emerald" className="mb-3">Architectural Principle</Badge>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">
              Why Separate Deterministic Math from AI?
            </h2>
            <p className="mt-3 text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
              Standard LLMs frequently calculate compounding interest, emergency runway months, and tax brackets incorrectly. ArthaAI isolates mathematical execution in Python and uses AI solely for regulatory reasoning and explanation.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="hover:border-emerald-500/50 transition-colors shadow-2xs">
              <CardContent className="p-6 space-y-4">
                <div className="w-10 h-10 rounded-lg bg-emerald-50 dark:bg-emerald-500/10 flex items-center justify-center text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20">
                  <LineChart className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">1. Deterministic Engine</h3>
                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  Computes exact monthly surplus, savings ratio, emergency fund adequacy, and SIP compounding requirements with zero floating-point errors.
                </p>
                <div className="text-xs text-emerald-700 dark:text-emerald-400 font-medium pt-2">
                  • 0–100 Weighted Risk Scoring<br />
                  • SEBI Allocation Bounds
                </div>
              </CardContent>
            </Card>

            <Card className="hover:border-sky-500/50 transition-colors shadow-2xs">
              <CardContent className="p-6 space-y-4">
                <div className="w-10 h-10 rounded-lg bg-sky-50 dark:bg-sky-500/10 flex items-center justify-center text-sky-700 dark:text-sky-400 border border-sky-200 dark:border-sky-500/20">
                  <Database className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">2. Knowledge RAG Pipeline</h3>
                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  Retrieves dense vector embeddings across official SEBI mutual fund guidelines, RBI deposit insurance (DICGC), and CBDT capital gains tax circulars.
                </p>
                <div className="text-xs text-sky-700 dark:text-sky-400 font-medium pt-2">
                  • PostgreSQL + pgvector<br />
                  • Exact Source Citations
                </div>
              </CardContent>
            </Card>

            <Card className="hover:border-amber-500/50 transition-colors shadow-2xs">
              <CardContent className="p-6 space-y-4">
                <div className="w-10 h-10 rounded-lg bg-amber-50 dark:bg-amber-500/10 flex items-center justify-center text-amber-800 dark:text-amber-400 border border-amber-200 dark:border-amber-500/20">
                  <Cpu className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">3. Explainable Portfolios</h3>
                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  Translates mathematical outputs and regulatory rules into clear, structured investment roadmaps with actionable monthly SIP allocations.
                </p>
                <div className="text-xs text-amber-800 dark:text-amber-400 font-medium pt-2">
                  • Goal Feasibility Analysis<br />
                  • Downside Protection Buffer
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20 border-t border-slate-200 dark:border-slate-800/80 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">How ArthaAI Works</h2>
            <p className="mt-3 text-sm text-slate-600 dark:text-slate-400">
              A 4-step streamlined workflow from financial input to verified portfolio execution.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[
              {
                step: "01",
                title: "Input Financial Profile",
                desc: "Provide income, monthly expenses, existing savings, and liabilities in INR.",
              },
              {
                step: "02",
                title: "Calculate Risk & Runway",
                desc: "The engine sizes an emergency fund buffer and scores risk capacity vs tolerance.",
              },
              {
                step: "03",
                title: "RAG Knowledge Retrieval",
                desc: "Semantic search checks relevant SEBI categories, debt rules, and tax exemptions.",
              },
              {
                step: "04",
                title: "Receive Roadmap",
                desc: "Get an actionable asset matrix (Equity, Debt, Gold, Cash) with exact SIP amounts.",
              },
            ].map((item) => (
              <div key={item.step} className="p-5 rounded-xl bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 shadow-2xs dark:shadow-none relative">
                <span className="text-3xl font-black text-slate-200 dark:text-slate-800 block mb-2">{item.step}</span>
                <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-200">{item.title}</h4>
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-2 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Security & Privacy */}
      <section id="security" className="py-20 border-t border-slate-200 dark:border-slate-800/80 bg-slate-50/60 dark:bg-slate-900/40 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto rounded-2xl bg-white dark:bg-gradient-to-b dark:from-slate-900 dark:to-slate-950 border border-slate-200 dark:border-slate-800 p-8 sm:p-12 text-center space-y-6 shadow-2xs dark:shadow-none">
            <div className="w-12 h-12 rounded-full bg-emerald-50 dark:bg-emerald-500/10 flex items-center justify-center text-emerald-700 dark:text-emerald-400 mx-auto border border-emerald-200 dark:border-emerald-500/20">
              <Lock className="w-6 h-6" />
            </div>

            <h3 className="text-2xl font-bold text-slate-900 dark:text-white">
              Data Privacy &amp; Statutory Transparency
            </h3>

            <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
              ArthaAI does not execute unauthorized trades or store banking credentials. All financial analysis is generated on demand with complete source transparency and mathematical reproducibility.
            </p>

            <div className="flex flex-wrap items-center justify-center gap-6 pt-2 text-xs text-slate-700 dark:text-slate-300">
              <span className="flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" /> Transparent Formulas</span>
              <span className="flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" /> SEBI-Aligned Categories</span>
              <span className="flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" /> No Unchecked AI Trading</span>
            </div>

            <div className="pt-4">
              <Link href="/dashboard">
                <Button size="lg" className="px-8 bg-emerald-600 hover:bg-emerald-500 text-white shadow-md">
                  Get Started with Dashboard
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
