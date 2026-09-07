import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ToastProvider } from "@/hooks/useToast";
import { FinancialDataProvider } from "@/hooks/useFinancialData";
import { Navbar } from "@/components/layout/Navbar";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "ArthaAI - AI-Powered Personal Finance & Investment Recommendation System",
  description:
    "Production-grade, explainable personal finance platform tailored for India (INR ₹). Deterministic SEBI financial rules, RAG knowledge retrieval, and personalized portfolios.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-slate-950 text-slate-100 antialiased min-h-screen flex flex-col`}>
        <ToastProvider>
          <FinancialDataProvider>
            <Navbar />
            <div className="flex-1 flex flex-col">{children}</div>
          </FinancialDataProvider>
        </ToastProvider>
      </body>
    </html>
  );
}
