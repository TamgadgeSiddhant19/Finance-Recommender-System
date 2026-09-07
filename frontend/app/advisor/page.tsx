"use client";

import React, { useState, useRef, useEffect } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ragService } from "@/services/ragService";
import { ChatMessage, RetrievedChunk } from "@/types";
import {
  Sparkles,
  Send,
  BookOpen,
  ShieldCheck,
  Building2,
  FileText,
  User,
  Bot,
  ExternalLink,
  HelpCircle,
} from "lucide-react";

const SUGGESTED_PROMPTS = [
  "What are the capital gains tax rates on equity mutual funds under Finance Act 2024?",
  "How does the DICGC ₹5 Lakh deposit insurance protect my bank fixed deposits?",
  "What is the SEBI allocation mandate for Large Cap vs Flexi Cap mutual funds?",
  "What are the tax benefits of investing in the National Pension System (NPS) Tier 1?",
  "Explain the Sovereign Gold Bond (SGB) 2.5% coupon and maturity capital gains exemption.",
];

export default function AdvisorPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "initial-1",
      sender: "assistant",
      content:
        "Hello! I am your AI Financial Regulatory & Advisory Assistant. I retrieve authentic guidelines and tax rules directly from SEBI, RBI, CBDT, and PFRDA to give you explainable, verified answers.\n\nHow can I help you today?",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [inputQuery, setInputQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (queryText: string) => {
    const text = queryText.trim();
    if (!text || isLoading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery("");
    setIsLoading(true);

    try {
      const response = await ragService.queryKnowledge({
        query: text,
        top_k: 3,
      });

      const aiMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        sender: "assistant",
        content: response.answer,
        sources: response.sources,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `error-${Date.now()}`,
        sender: "assistant",
        content:
          "I encountered an issue retrieving live data from the knowledge base. Please ensure the backend is running or try again.",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 flex min-h-[calc(100vh-4rem)]">
      <Sidebar />

      <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-5xl mx-auto flex flex-col space-y-4">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-800">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-emerald-400" />
              AI Regulatory & Financial Advisor
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Grounded on official Indian statutory documents (SEBI, RBI, CBDT, PFRDA) using dense vector RAG.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="blue" size="sm">
              <BookOpen className="w-3 h-3 mr-1" />
              pgvector RAG
            </Badge>
            <Badge variant="emerald" size="sm">
              <ShieldCheck className="w-3 h-3 mr-1" />
              Grounded AI
            </Badge>
          </div>
        </div>

        {/* Chat Message Window */}
        <Card className="flex-1 flex flex-col min-h-[500px] max-h-[680px] overflow-hidden bg-slate-950/70 border-slate-800">
          <CardContent className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5">
            {messages.map((msg) => {
              const isUser = msg.sender === "user";

              return (
                <div
                  key={msg.id}
                  className={`flex gap-3 max-w-3xl ${isUser ? "ml-auto flex-row-reverse" : "mr-auto"}`}
                >
                  <div
                    className={`w-8 h-8 rounded-full shrink-0 flex items-center justify-center text-xs font-bold ${
                      isUser
                        ? "bg-emerald-600 text-white"
                        : "bg-slate-800 text-emerald-400 border border-emerald-500/30"
                    }`}
                  >
                    {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                  </div>

                  <div className="space-y-2 flex-1">
                    <div
                      className={`p-4 rounded-2xl text-xs sm:text-sm leading-relaxed ${
                        isUser
                          ? "bg-emerald-600 text-white rounded-tr-none"
                          : "bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none shadow-md"
                      }`}
                    >
                      <div className="whitespace-pre-wrap">{msg.content}</div>
                    </div>

                    {/* Source Citations Section */}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="space-y-1.5 pt-1">
                        <p className="text-[11px] font-semibold text-slate-400 flex items-center gap-1">
                          <Building2 className="w-3 h-3 text-sky-400" />
                          Retrieved Regulatory Sources ({msg.sources.length}):
                        </p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {msg.sources.map((src, sIdx) => (
                            <div
                              key={sIdx}
                              className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800 text-[11px] text-slate-300 space-y-1"
                            >
                              <div className="flex items-center justify-between">
                                <span className="font-semibold text-emerald-300 truncate">
                                  {src.organization}
                                </span>
                                <span className="text-[10px] text-sky-400 font-mono">
                                  {Math.round(src.similarity_score * 100)}% match
                                </span>
                              </div>
                              <p className="text-slate-400 truncate text-[10px]">{src.document_title}</p>
                              <p className="text-slate-300 line-clamp-2 italic text-[10px] pt-0.5">
                                &ldquo;{src.content}&rdquo;
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {isLoading && (
              <div className="flex gap-3 max-w-3xl mr-auto">
                <div className="w-8 h-8 rounded-full bg-slate-800 text-emerald-400 border border-emerald-500/30 flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4 animate-pulse" />
                </div>
                <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 text-slate-400 text-xs rounded-tl-none flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                  Retrieving regulatory vector chunks & synthesizing grounded response...
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </CardContent>

          {/* Quick Suggested Prompts */}
          <div className="p-3 border-t border-slate-800/80 bg-slate-950/90">
            <div className="flex items-center gap-1.5 overflow-x-auto pb-2 scrollbar-none">
              <span className="text-[10px] font-semibold text-slate-400 shrink-0 flex items-center gap-1 mr-1">
                <HelpCircle className="w-3 h-3 text-emerald-400" />
                Suggested:
              </span>
              {SUGGESTED_PROMPTS.map((prompt, pIdx) => (
                <button
                  key={pIdx}
                  onClick={() => handleSendMessage(prompt)}
                  className="shrink-0 text-[11px] px-2.5 py-1 rounded-full bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-emerald-300 border border-slate-800 transition-colors cursor-pointer"
                >
                  {prompt.length > 45 ? `${prompt.substring(0, 45)}...` : prompt}
                </button>
              ))}
            </div>

            {/* Input Box */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage(inputQuery);
              }}
              className="flex items-center gap-2 mt-2"
            >
              <input
                type="text"
                placeholder="Ask about SEBI mutual fund rules, Indian tax slabs, SGBs, or deposit insurance..."
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                disabled={isLoading}
                className="flex-1 rounded-lg bg-slate-900 border border-slate-700/80 px-4 py-2.5 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              />
              <Button type="submit" disabled={!inputQuery.trim() || isLoading} className="gap-1.5 px-4 shrink-0">
                <Send className="w-4 h-4" />
                <span className="hidden sm:inline">Ask</span>
              </Button>
            </form>
          </div>
        </Card>
      </main>
    </div>
  );
}
