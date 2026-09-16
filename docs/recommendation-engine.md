# Phase 6 & Phase 7.2: Goal-Aware Deterministic Financial Recommendation Engine

A production-grade, explainable, and 100% deterministic portfolio recommendation subsystem engineered for the **Indian Financial Ecosystem (INR ₹)**, with multi-goal awareness, horizon policy buckets, inflation indexation, and feasibility guardrails.

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
                  │
                  ▼
   4. Deterministic Product Scoring (`scoring.py`)
   • Risk Fit Score (0–100, 35% weight)
   • Horizon Fit Score (0–100, 25% weight)
   • Asset Class Alignment (0–100, 20% weight)
   • Cost / TER Efficiency (0–100, 10% weight)
   • Ticket Sizing Compatibility (0–100, 10% weight)
                  │
                  ▼
   5. Portfolio Construction (`portfolio.py`)
   • Ranks top eligible instruments per asset class
   • Distributes exact percentage weights and rupee SIP / lump sum amounts
   • Produces structured selection rationales for each instrument
                  │
                  ▼
   6. Portfolio Validation (`validators.py`)
   • Verifies sum(allocations) == 100.00% (within ±0.5% tolerance)
   • Validates total SIP <= user monthly investment capacity
   • Confirms zero ineligible instruments and risk guardrail compliance
                  │
                  ▼
   7. Persistence & Response (`models.py`, `service.py`, `endpoints/recommendations.py`)
   • Persists audit trail in `recommendations` & `recommendation_items` tables
   • Returns goal-aware metrics, rationale, funding actions, and per-goal breakdowns
```

---

## ⚖️ Core Principles & Guardrails

1. **Zero Hallucination Risk**: Asset allocations, rupee calculations, compounding math, and explanations are computed strictly by deterministic Python algorithms. Zero LLM involvement in decision logic.
2. **Horizon-Based Capital Defense**:
   - Short-term goals (< 3 years): Curtails equity (10%–25%) and prioritizes capital preservation via debt (55%–70%) and cash/liquid (15%).
   - Medium-term goals (3–5 years): Balances growth with volatility dampening.
   - Long-term goals (> 5 years): Allows higher growth allocations (up to 85% equity for aggressive profiles) to beat inflation.
3. **Strict Risk Guardrails**: Goal horizon adjustments can NEVER breach the user's hard risk category ceiling (e.g., a Conservative profile with a 15-year goal is strictly capped at 30% equity).
4. **Funding-Gap Safety Rule**: An underfunded goal (`MODERATELY_UNDERFUNDED`, `SIGNIFICANTLY_UNDERFUNDED`, or `NOT_FEASIBLE`) must **NEVER** cause the engine to recommend higher-risk speculative assets. Actionable mathematical solutions (e.g. increase monthly SIP, extend timeline, re-scope target) are provided instead.

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
