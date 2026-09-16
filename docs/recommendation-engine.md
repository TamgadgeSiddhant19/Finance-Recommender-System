# Phase 6, Phase 7.2 & Phase 7.3: Goal-Aware Deterministic Financial Recommendation & Product Intelligence Engine

A production-grade, explainable, and 100% deterministic portfolio recommendation subsystem engineered for the **Indian Financial Ecosystem (INR ₹)**, with multi-goal awareness, horizon policy buckets, inflation indexation, feasibility guardrails, and data-informed **Product Intelligence & Suitability Ranking**.

---

## 🏛️ System Architecture

```
User Profile, Goals & Financial Products (DB)
                  │
                  ▼
   1. Goal Horizon & Feasibility Engine (`calculator.py`, `policy.py`)
   • Computes inflation-adjusted targets compounding at 6.0% p.a.
   • Computes future value of savings & monthly SIP (Annuity Due)
   • Classifies Feasibility: ON_TRACK, MODERATELY_UNDERFUNDED, SIGNIFICANTLY_UNDERFUNDED, NOT_FEASIBLE
   • Classifies Horizon Bucket: SHORT_TERM (<3 yrs), MEDIUM_TERM (3–5 yrs), LONG_TERM (>5 yrs)
                  │
                  ▼
   2. Goal-Aware Target Asset Allocation (`allocation.py`, `policy.py`)
   • Applies horizon policy matrix (Equity, Debt, Gold, Cash)
   • Enforces hard risk ceilings (e.g., Conservative equity <= 30%)
   • Normalizes weights with Decimal arithmetic to exactly 100.00%
   • Generates deterministic explanation templates per asset class
                  │
                  ▼
   3. Eligibility Filtering (`filters.py`)
   • Excludes products exceeding risk boundaries (e.g. high/very_high for conservative profiles)
   • Enforces ticket size compatibility (min_investment <= investment capacity)
   • Validates currency (INR) and domicile
   • Captures structured exclusion audit log (`excluded_products`)
                  │
                  ▼
   4. Product Intelligence & Market Historical Analytics (`product_intelligence.py`)
   • Reuses `app/market/intelligence/analytics.py` (Returns, Volatility, Drawdown)
   • Fetches candles via `MarketDataService` (Alpha Vantage / Demo adapters)
   • Computes 1Y, 3Y, 5Y historical returns, annualized volatility, max drawdown, and data quality score
   • Tracks full data provenance (`data_source`, `data_status`, `data_as_of`)
                  │
                  ▼
   5. Deterministic Suitability Scoring (`scoring.py`, `constants.py`)
   • Risk Fit Score (25% weight)
   • Horizon Fit Score (20% weight)
   • Asset Class Fit Score (20% weight)
   • Financial Goal Fit Score (10% weight)
   • Cost / TER Efficiency (10% weight)
   • Ticket Sizing Compatibility (5% weight)
   • Market Performance Fit (5% weight — with anti-return-chasing volatility/drawdown penalties)
   • Data Quality Score (5% weight)
                  │
                  ▼
   6. Portfolio Construction (`portfolio.py`)
   • Ranks top eligible instruments per asset class based on total suitability score
   • Distributes exact percentage weights and rupee SIP / lump sum amounts
   • Attaches rich intelligence metadata and transparent multi-factor selection reasons
                  │
                  ▼
   7. Portfolio Validation (`validators.py`)
   • Verifies sum(allocations) == 100.00% (within ±0.5% tolerance)
   • Validates total SIP <= user monthly investment capacity
   • Confirms zero ineligible instruments and risk guardrail compliance
                  │
                  ▼
   8. Persistence & Response (`models.py`, `service.py`, `endpoints/recommendations.py`)
   • Persists audit trail in `recommendations` & `recommendation_items` tables with JSON intelligence metadata
   • Returns goal-aware metrics, rationale, funding actions, excluded products, and per-goal breakdowns
```

---

## ⚖️ Core Principles & Guardrails

1. **Zero Hallucination Risk**: Asset allocations, rupee calculations, compounding math, and explanations are computed strictly by deterministic Python algorithms. Zero LLM involvement in decision logic.
2. **Horizon-Based Capital Defense**:
   - Short-term goals (< 3 years): Curtails equity (10%–25%) and prioritizes capital preservation via debt (55%–70%) and cash/liquid (15%).
   - Medium-term goals (3–5 years): Balances growth with volatility dampening.
   - Long-term goals (> 5 years): Allows higher growth allocations (up to 85% equity for aggressive profiles) to beat inflation.
3. **Strict Risk Guardrails**: Goal horizon adjustments can NEVER breach the user's hard risk category ceiling (e.g., a Conservative profile with a 15-year goal is strictly capped at 30% equity).
4. **Anti-Return-Chasing Mechanism**: Market performance weight is strictly bounded at 5% of total score. High returns with high volatility (>20% ann.) or deep drawdowns (< -25%) receive severe penalties.
5. **Data Provenance & Transparency**: Data origins are clearly tagged as `alphavantage` (`live`/`historical`) or `demo` (`synthetic`). Synthetic data is never misrepresented as real market data.
6. **Exclusion Audit Trail**: Products screened out during filtering or scoring provide structured audit reasons explaining why they were not selected.

---

## 🎯 Centralized Goal-Aware Allocation Matrix

| Risk Profile | Horizon Bucket | Target Equity | Target Debt | Target Gold | Target Cash |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CONSERVATIVE** | **SHORT_TERM (<3y)** | 10.00% | 70.00% | 5.00% | 15.00% |
| **CONSERVATIVE** | **MEDIUM_TERM (3-5y)** | 20.00% | 65.00% | 10.00% | 5.00% |
| **CONSERVATIVE** | **LONG_TERM (>5y)** | 30.00% | 60.00% | 10.00% | 0.00% |
| **MODERATE** | **SHORT_TERM (<3y)** | 15.00% | 65.00% | 5.00% | 15.00% |
| **MODERATE** | **MEDIUM_TERM (3-5y)** | 45.00% | 45.00% | 10.00% | 0.00% |
| **MODERATE** | **LONG_TERM (>5y)** | 55.00% | 35.00% | 10.00% | 0.00% |
| **AGGRESSIVE** | **SHORT_TERM (<3y)** | 20.00% | 60.00% | 5.00% | 15.00% |
| **AGGRESSIVE** | **MEDIUM_TERM (3-5y)** | 60.00% | 30.00% | 10.00% | 0.00% |
| **AGGRESSIVE** | **LONG_TERM (>5y)** | 75.00% | 15.00% | 10.00% | 0.00% |
| **VERY_AGGRESSIVE**| **SHORT_TERM (<3y)** | 25.00% | 55.00% | 5.00% | 15.00% |
| **VERY_AGGRESSIVE**| **MEDIUM_TERM (3-5y)** | 70.00% | 20.00% | 10.00% | 0.00% |
| **VERY_AGGRESSIVE**| **LONG_TERM (>5y)** | 85.00% | 10.00% | 5.00% | 0.00% |

---

## 📊 Product Intelligence Scoring Weights

| Component | Weight | Deterministic Criteria |
| :--- | :--- | :--- |
| **Risk Fit** | 25.00% | Match between user risk tolerance and instrument SEBI risk tier |
| **Horizon Fit** | 20.00% | Instrument asset class lock-in / compounding horizon alignment |
| **Asset Class Fit** | 20.00% | Target asset class allocation priority (Equity, Debt, Gold, Cash) |
| **Goal Fit** | 10.00% | Purpose alignment (Retirement, House, Education, Wealth) |
| **Cost Efficiency** | 10.00% | Total Expense Ratio (TER) drag minimization (<0.25% TER = 90 pts) |
| **Ticket Sizing** | 5.00% | Minimum investment size vs. monthly investment capacity |
| **Market Performance** | 5.00% | Risk-adjusted 1Y return with volatility and drawdown penalties |
| **Data Quality** | 5.00% | Sample count, history depth, and provenance verification score |


---

## 💡 Funding Gap Decision Rules

- **ON_TRACK (Funding Ratio $\ge 100\%$)**:
  Maintain regular goal/risk allocation. Review assumptions semi-annually.
- **MODERATELY_UNDERFUNDED (Funding Ratio $75\% - 99.9\%$)**:
  Calculate exact monthly contribution increase to close gap; offer option to extend timeline by 1–2 years; keep portfolio risk unchanged.
- **SIGNIFICANTLY_UNDERFUNDED (Funding Ratio $40\% - 74.9\%$)**:
  Recommend monthly contribution step-up (10% annual escalation); recommend target re-evaluation or timeline extension; strictly forbid chasing returns via higher risk.
- **NOT_FEASIBLE (Funding Ratio $< 40\%$)**:
  Flag goal as requiring intervention; advise prioritizing core emergency/retirement goals or extending investment horizon significantly; do not assume unrealistic market returns.

---

## ⚠️ Regulatory Financial Disclaimer & Limitations

> [!NOTE]
> **Educational & Decision-Support Calculation**:
> The Artha AI recommendation engine provides deterministic mathematical modeling and educational decision-support analysis.
> Expected return assumptions and inflation models are for projection purposes only and do not constitute guaranteed returns, profit forecasts, or registered investment advisory solicitations. Market investments are subject to market risks.
