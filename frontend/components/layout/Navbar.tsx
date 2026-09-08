"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { TrendingUp, Sparkles, Menu, X, ArrowRight, User, LogOut, LogIn, Sun, Moon } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useFinancialData } from "@/hooks/useFinancialData";
import { useAuth } from "@/hooks/useAuth";
import { useTheme } from "@/hooks/useTheme";

export function Navbar() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { isBackendConnected } = useFinancialData();
  const { user, isAuthenticated, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  const isAppRoute = pathname !== "/" && pathname !== "/login" && pathname !== "/register";

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 dark:border-slate-800/80 bg-white/90 dark:bg-slate-950/80 backdrop-blur-md transition-colors">
      <div className="max-w-7xl mx-auto flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-600 shadow-sm text-white font-bold text-lg">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="text-base font-bold tracking-tight text-slate-900 dark:text-white">Artha<span className="text-emerald-600 dark:text-emerald-400">AI</span></span>
              <span className="hidden sm:inline-block ml-1.5 text-[10px] font-semibold text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700/60 bg-slate-50 dark:bg-transparent px-1.5 py-0.5 rounded">
                INDIA • INR ₹
              </span>
            </div>
          </Link>

          {!isAppRoute && (
            <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600 dark:text-slate-300">
              <Link href="#features" className="hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">Features</Link>
              <Link href="#how-it-works" className="hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">How It Works</Link>
              <Link href="#security" className="hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">Security & Ethics</Link>
            </nav>
          )}
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={toggleTheme}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-900 hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors cursor-pointer border border-slate-200 dark:border-slate-800 shadow-xs"
            title={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
            aria-label="Toggle Theme"
          >
            {theme === "dark" ? (
              <>
                <Sun className="w-3.5 h-3.5 text-amber-400" />
                <span className="hidden sm:inline text-[11px]">Light</span>
              </>
            ) : (
              <>
                <Moon className="w-3.5 h-3.5 text-emerald-600" />
                <span className="hidden sm:inline text-[11px]">Dark</span>
              </>
            )}
          </button>

          {isAuthenticated && user ? (
            <div className="flex items-center gap-2">
              <div className="hidden md:flex items-center gap-2 px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs text-slate-700 dark:text-slate-300">
                <div className="w-5 h-5 rounded-full bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400 flex items-center justify-center font-bold text-[10px]">
                  {user.full_name ? user.full_name.charAt(0).toUpperCase() : user.email.charAt(0).toUpperCase()}
                </div>
                <span className="font-medium text-slate-800 dark:text-slate-200 truncate max-w-[120px]">
                  {user.full_name || user.email.split("@")[0]}
                </span>
              </div>

              {isAppRoute && (
                <Link href="/advisor">
                  <Button size="sm" variant="outline" className="border-emerald-500/40 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-50 dark:hover:bg-emerald-500/10 gap-1.5 hidden sm:inline-flex">
                    <Sparkles className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                    AI Advisor
                  </Button>
                </Link>
              )}

              <Button
                size="sm"
                variant="ghost"
                onClick={logout}
                className="text-slate-600 dark:text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-500/10 gap-1.5"
                title="Log Out"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Logout</span>
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link href="/login">
                <Button size="sm" variant="ghost" className="text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white gap-1.5">
                  <LogIn className="w-3.5 h-3.5" />
                  Sign In
                </Button>
              </Link>
              <Link href="/register">
                <Button size="sm" variant="primary" className="gap-1.5">
                  Register
                  <ArrowRight className="w-3.5 h-3.5" />
                </Button>
              </Link>
            </div>
          )}

          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 p-1.5 ml-1"
            aria-label="Toggle Navigation"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-slate-900/95 px-4 py-4 space-y-3">
          <Link
            href="/"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-sm font-medium text-slate-800 dark:text-slate-200 py-1"
          >
            Home
          </Link>
          <Link
            href="/dashboard"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-sm font-medium text-emerald-600 dark:text-emerald-400 py-1"
          >
            Dashboard
          </Link>
          <Link
            href="/profile"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-sm font-medium text-slate-800 dark:text-slate-200 py-1"
          >
            Financial Profile
          </Link>
          <Link
            href="/advisor"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-sm font-medium text-slate-800 dark:text-slate-200 py-1"
          >
            AI Financial Advisor
          </Link>
          {isAuthenticated ? (
            <button
              onClick={() => {
                setMobileMenuOpen(false);
                logout();
              }}
              className="block w-full text-left text-sm font-medium text-rose-600 dark:text-rose-400 py-1"
            >
              Sign Out ({user?.email})
            </button>
          ) : (
            <div className="pt-2 border-t border-slate-200 dark:border-slate-800 flex gap-2">
              <Link
                href="/login"
                onClick={() => setMobileMenuOpen(false)}
                className="block text-sm font-medium text-emerald-600 dark:text-emerald-400 py-1"
              >
                Sign In
              </Link>
              <span className="text-slate-400">|</span>
              <Link
                href="/register"
                onClick={() => setMobileMenuOpen(false)}
                className="block text-sm font-medium text-slate-800 dark:text-slate-200 py-1"
              >
                Register
              </Link>
            </div>
          )}
        </div>
      )}
    </header>
  );
}

