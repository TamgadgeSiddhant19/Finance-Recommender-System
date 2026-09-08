import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ToastProvider } from "@/hooks/useToast";
import { AuthProvider } from "@/hooks/useAuth";
import { FinancialDataProvider } from "@/hooks/useFinancialData";
import { ThemeProvider } from "@/hooks/useTheme";
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
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={`${inter.className} bg-background text-foreground antialiased min-h-screen flex flex-col transition-colors duration-200`}>
        <ThemeProvider>
          <ToastProvider>
            <AuthProvider>
              <FinancialDataProvider>
                <Navbar />
                <div className="flex-1 flex flex-col">{children}</div>
              </FinancialDataProvider>
            </AuthProvider>
          </ToastProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
