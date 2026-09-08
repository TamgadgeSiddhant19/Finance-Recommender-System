# Phase 6: Deterministic Financial Recommendation Engine

A production-grade, explainable, and 100% deterministic portfolio recommendation subsystem engineered for the **Indian Financial Ecosystem (INR ₹)**.

---

## 🏛️ System Architecture

```
User Profile, Goals & Financial Products (DB)
                  │
                  ▼
   1. Eligibility Filtering (`filters.py`)
   • Excludes products exceeding risk boundaries (e.g. high/very_high for conservative profiles)
   • Enforces ticket size compatibility (min_investment <= investment capacity)
   • Validates currency (INR) and domicile
                  │
                  ▼
   2. Deterministic Scoring (`scoring.py`)
   • Risk Fit Score (0–100, 35% weight)
   • Horizon Fit Score (0–100, 25% weight)
   • Asset Class Alignment (0–100, 20% weight)
   • Cost / TER Efficiency (0–100, 10% weight)
   • Ticket Sizing Compatibility (0–100, 10% weight)
                  │
                  ▼
   3. Target Asset Allocation (`allocation.py`)
   • SEBI-aligned bounds (Conservative, Moderate, Aggressive, Very Aggressive)
   • Dynamic horizon dampener for short-term goals (< 3 years)
                  │
                  ▼
   4. Portfolio Construction (`portfolio.py`)
   • Ranks top eligible instruments per asset class
   • Distributes exact percentage weights and rupee SIP / lump sum amounts
   • Produces structured selection rationales for each instrument
                  │
                  ▼
   5. Portfolio Validation (`validators.py`)
   • Verifies sum(allocations) == 100.00% (within ±0.5% tolerance)
   • Validates total SIP <= user monthly investment capacity
   • Confirms zero ineligible instruments and risk guardrail compliance
                  │
                  ▼
   6. Persistence & Response (`models.py`, `service.py`, `api.py`)
   • Persists audit trail in `recommendations` & `recommendation_items` tables
   • Returns structured response + prepared payload for downstream RAG explanation
```

---

## ⚖️ Why Deterministic Logic Instead of LLM Decision-Making?

1. **Zero Hallucination Risk**: Asset allocations, rupee calculations, and compounding math are computed strictly by audited Python algorithms.
2. **Explainability & Auditability**: Every product selected has exact numerical scores and traceable factor contributions.
3. **Regulatory Safety (SEBI / PFRDA / RBI Alignment)**: Guardrails prevent high-risk speculative instruments from being recommended to conservative profiles.
4. **Separation of Concerns**: Gemini and the RAG pipeline are positioned downstream solely for natural language synthesis and regulatory citation explanation, never for quantitative asset allocation.

---

## 📐 Scoring Methodology

$$\text{Suitability Score} = (0.35 \times S_{\text{risk}}) + (0.25 \times S_{\text{horizon}}) + (0.20 \times S_{\text{asset}}) + (0.10 \times S_{\text{cost}}) + (0.10 \times S_{\text{compat}})$$

### 1. Risk Fit Score ($S_{\text{risk}}$, Weight = 35%)
- **Exact Match** (e.g. Moderate user $\rightarrow$ Moderate product): **100**
- **1-step Distance** (e.g. Moderate user $\rightarrow$ Low or High product): **75**
- **2-step Distance** (e.g. Aggressive user $\rightarrow$ Low product): **50**
- **3-step Distance**: **25**

### 2. Goal Horizon Fit Score ($S_{\text{horizon}}$, Weight = 25%)
- **Short-term (< 3 years)**: Debt / Liquid / FD / T-Bill (**95**), Gold (**65**), Hybrid (**60**), Pure Equity (**40**)
- **Medium-term (3–7 years)**: Hybrid (**95**), Index / Large Cap Equity (**85**), Gold (**85**), Debt (**75**)
- **Long-term (> 7 years)**: Equity Index / Flexi-Cap (**95**), Hybrid / Gold (**80**), Debt (**60**)

### 3. Asset Class Fit Score ($S_{\text{asset}}$, Weight = 20%)
- Core target asset ($\ge 50\%$ target allocation): **100**
- Major target asset ($20\% - 49\%$ target allocation): **85**
- Satellite stabilizer ($1\% - 19\%$ target allocation): **70**
- Zero target allocation: **30**

### 4. Cost / TER Efficiency ($S_{\text{cost}}$, Weight = 10%)
- 0.00% TER / Sovereign instrument (PPF, SGB, direct stocks): **95**
- $\le 0.25\%$ TER (Low-cost Index ETF): **90**
- $\le 0.50\%$ TER (Efficient Mutual Fund): **80**
- $\le 0.80\%$ TER: **65**
- $> 0.80\%$ TER: **50**

### 5. Ticket Sizing Compatibility ($S_{\text{compat}}$, Weight = 10%)
- $\text{Minimum Investment} \le 20\%$ of monthly capacity: **95**
- $\text{Minimum Investment} \le 50\%$ of monthly capacity: **80**
- $\text{Minimum Investment} \le 100\%$ of monthly capacity: **60**
- $\text{Minimum Investment} > \text{monthly capacity}$: **20**

---

## 🎯 Target Asset Allocation Matrices

| Risk Profile | Domestic Equities | Debt & Fixed Income | Gold & Commodities | Cash / Liquid Buffer |
| :--- | :--- | :--- | :--- | :--- |
| **Conservative** | 25.00% | 65.00% | 5.00% | 5.00% |
| **Moderate** | 55.00% | 35.00% | 10.00% | 0.00% |
| **Aggressive** | 75.00% | 15.00% | 10.00% | 0.00% |
| **Very Aggressive** | 85.00% | 10.00% | 5.00% | 0.00% |

*Note: For users with short average goal horizons (< 3 years), equity exposure is automatically capped at 25% max with excess reallocated to debt and cash.*

---

## 🛡️ Portfolio Validation Checks

1. **Total Allocation Sum (100%)**: Verifies $\sum \text{Weights} = 100.00\% \pm 0.5\%$.
2. **Investment Capacity Ceiling**: Verifies $\sum \text{Monthly SIP} \le \text{User Monthly Capacity} + 1\text{ INR}$.
3. **Product Eligibility Verification**: Confirms all instruments belong to the filtered eligible set.
4. **Risk Profile Guardrails**: Confirms no instrument risk rating exceeds user category bounds.
5. **Asset Class Fidelity**: Confirms portfolio asset distribution matches target model.

---

## 🔌 API Reference

### 1. Generate & Persist Recommendation
`POST /api/v1/recommendations/{user_id}`

**Response (201 Created)**:
```json
{
  "recommendation_id": 1,
  "user_id": 1,
  "risk_category": "MODERATE",
  "risk_score": 55,
  "monthly_investment_capacity": 25000.00,
  "target_allocation": {
    "equity_pct": 55.00,
    "debt_pct": 35.00,
    "gold_pct": 10.00,
    "cash_pct": 0.00
  },
  "portfolio_items": [
    {
      "product_id": 1,
      "symbol": "NIFTY50-INDX",
      "name": "Nifty 50 Index Fund",
      "product_type": "index_fund",
      "asset_class": "equity",
      "risk_level": "high",
      "suitability_score": 88.50,
      "allocation_percentage": 30.25,
      "suggested_monthly_sip": 7562.50,
      "suggested_lump_sum": 0.00,
      "selection_reasons": [
        {
          "category": "Risk Suitability",
          "description": "Adjacent risk rating (HIGH is suitable for MODERATE profile)",
          "score_contribution": 26.25
        },
        {
          "category": "Cost Efficiency",
          "description": "Ultra-low expense ratio (0.20% TER minimizes return drag)",
          "score_contribution": 9.00
        }
      ]
    }
  ],
  "total_monthly_sip": 25000.00,
  "total_lump_sum": 0.00,
  "validation_report": {
    "is_valid": true,
    "checks": [
      {
        "check_name": "Total Allocation Sum (100%)",
        "passed": true,
        "details": "Total asset weights sum to 100.00% (Within ±0.50% tolerance)."
      },
      {
        "check_name": "Investment Capacity Ceiling",
        "passed": true,
        "details": "Total SIP deployment (₹25,000.00) is within monthly capacity (₹25,000.00)."
      }
    ],
    "error_messages": [],
    "warning_messages": []
  },
  "created_at": "2026-09-08T12:00:00Z"
}
```

### 2. Stateless Simulation
`POST /api/v1/recommendations/simulate`
Accepts `RecommendationSimulateRequest` payload without database persistence.

---

## 🔮 Future RAG & Gemini Integration Interface

The recommendation engine provides `RecommendationService.prepare_rag_explanation_payload(...)` which produces an audited structured snapshot for downstream LLM prompt synthesis:

```
Deterministic Portfolio + Selection Reasons + User Profile
                           │
                           ▼
          RAG Regulatory Document Retrieval
    (SEBI MF Regulations, CBDT Section 112A, RBI SGB)
                           │
                           ▼
                 Gemini 1.5 Flash
             (Narrative Synthesis & Advice)
```
