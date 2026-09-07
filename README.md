# AI-Powered Personal Finance & Investment Recommendation System

A production-grade, explainable personal finance platform tailored for the **Indian Financial Market** (Currency: **INR ₹**).

---

## 📌 Project Overview

This platform empowers individuals to input their financial profile, income, expenses, savings, investment horizons, and risk tolerance to obtain personalized, mathematically robust, and regulatory-aware portfolio recommendations.

### Key Highlights
- **Target Market**: India (INR `₹`)
- **Core Principle**: **Strict Separation of Deterministic Math & AI Reasoning**.
  - **Deterministic Business Logic (Phase 3)**: Handles all quantitative calculations, multi-factor risk scoring (0–100), emergency fund buffer sizing, asset allocation matrix (SEBI-aligned bounds, debt-equity-gold balancing), and compounding annuity goal feasibility formulas.
  - **Financial Data Layer (Phase 4)**: Normalized product catalog and historical OHLCV market price series with pluggable adapter interfaces.
  - **Financial Knowledge RAG Pipeline (Phase 5)**: Authentic semantic retrieval and grounded natural language synthesis over official Indian regulatory documentation (SEBI, RBI, CBDT, PFRDA) using Sentence Transformers and PostgreSQL vector storage.
  - **Frontend UI Platform (Next.js + Tailwind + Recharts)**: Premium, dark fintech SaaS interface with live interactive charts, multi-factor risk gauge, goal tracking, and ChatGPT-style AI regulatory advisor.

---

## 🏛️ Project Structure

```
Finance-system/
├── frontend/                           # Next.js 16 App Router Frontend
│   ├── app/
│   │   ├── layout.tsx                  # Root layout with Toast & Financial data providers
│   │   ├── globals.css                 # Fintech dark tokens & Tailwind CSS
│   │   ├── page.tsx                    # 1. Landing Page (Hero, Features, Security, CTA)
│   │   ├── dashboard/page.tsx          # 2. Main Dashboard (Net position, Cashflow, KPIs)
│   │   ├── profile/page.tsx            # 3. Financial Profile Form (Live surplus & runway)
│   │   ├── goals/page.tsx              # 4. Goals Tracker (SIP required & progress)
│   │   ├── risk/page.tsx               # 5. Risk Assessment (0-100 Gauge & 4 Dimensions)
│   │   ├── portfolio/page.tsx          # 6. Target Portfolio (Recharts Donut & Catalog)
│   │   ├── advisor/page.tsx            # 7. AI Regulatory Advisor (Chatbot + Citations)
│   │   └── recommendations/page.tsx    # 8. Recommendation Report & Statutory Sources
│   ├── components/
│   │   ├── layout/ (Navbar, Sidebar, Footer)
│   │   ├── ui/ (Button, Card, Badge, Input, Select, Progress, Skeleton, Toast)
│   │   └── charts/ (AllocationPieChart, MonthlyCashflowChart)
│   ├── lib/ (utils.ts, mockData.ts)
│   ├── services/ (api.ts, profileService.ts, goalsService.ts, analysisService.ts, productsService.ts, ragService.ts)
│   ├── types/ (financial.ts, product.ts, rag.ts, index.ts)
│   └── hooks/ (useFinancialData.tsx, useToast.tsx)
├── backend/                            # FastAPI Python Backend
│   ├── app/
│   │   ├── api/v1/endpoints/ (health, users, profile, goals, analysis, financial_products, rag)
│   │   ├── core/config.py
│   │   ├── database/ (base.py, session.py)
│   │   ├── models/ (user, profile, goal, financial_product, market_data, rag)
│   │   ├── schemas/ (user, profile, goal, engine, financial_data, rag)
│   │   ├── services/ (engine, financial_health, risk_scoring, asset_allocation, goal_analyzer)
│   │   ├── financial_data/ (adapters, normalizer, validators, repository, ingestion)
│   │   └── rag/ (chunking, embeddings, retriever, llm, service, loaders)
│   ├── alembic/
│   └── tests/ (49 automated unit and integration tests)
├── data/
│   ├── financial_products.csv
│   ├── market_data.csv
│   └── documents/ (SEBI, RBI, CBDT, PFRDA authentic regulatory text/HTML)
└── docs/ (financial-data-layer.md, rag.md)
```

---

## 🚀 How to Run the System

### 1. Run the Backend API (FastAPI)
```powershell
cd backend
.\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```
- Interactive Swagger API Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Database Health Check: [http://127.0.0.1:8000/api/v1/health/db](http://127.0.0.1:8000/api/v1/health/db)

### 2. Run the Frontend (Next.js)
```powershell
cd frontend
npm run dev
```
- Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 📱 Frontend Page Routing & API Mapping

| Route | Page Name | Active API Integration / Fallback Mode |
| :--- | :--- | :--- |
| `/` | Landing Page | Static Marketing & Architectural Showcase |
| `/dashboard` | Main Overview | Connected to `GET /api/v1/analysis/{id}`, `GET /api/v1/profile/{id}`, `GET /api/v1/goals/{id}` |
| `/profile` | Financial Profile | Connected to `PUT /api/v1/profile/{id}` & `POST /api/v1/analysis/simulate` |
| `/goals` | Financial Goals | Connected to `GET /api/v1/goals/{id}` & `POST /api/v1/goals` |
| `/risk` | Risk Assessment | Connected to `GET /api/v1/analysis/{id}` (Risk Breakdown & Guardrails) |
| `/portfolio` | Target Portfolio | Connected to `GET /api/v1/analysis/{id}` & `GET /api/v1/financial-products` |
| `/advisor` | AI Regulatory Advisor | Connected to `POST /api/v1/rag/query` with live RAG vector search & citations |
| `/recommendations`| Official Advice Report | Connected to `GET /api/v1/analysis/{id}` (SEBI allocation & rationale) |
