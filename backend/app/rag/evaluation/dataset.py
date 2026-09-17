from typing import Any, Dict, List

BENCHMARK_DATASET: List[Dict[str, Any]] = [
    # 1. SEBI Mutual Funds
    {
        "id": "eval-sebi-01",
        "category": "sebi_mutual_funds",
        "query": "What is the mandatory equity allocation and market cap definition for Large Cap mutual funds under SEBI rules?",
        "expected_organization": "SEBI",
        "expected_topic": "mutual_funds",
        "expected_keywords": ["80%", "top 100", "large cap"],
        "is_out_of_domain": False,
        "requires_multi_chunk": False,
    },
    {
        "id": "eval-sebi-02",
        "category": "sebi_mutual_funds",
        "query": "What is the minimum equity investment percentage for Mid Cap and Small Cap funds according to SEBI?",
        "expected_organization": "SEBI",
        "expected_topic": "mutual_funds",
        "expected_keywords": ["65%", "101st to 250th", "251st"],
        "is_out_of_domain": False,
        "requires_multi_chunk": False,
    },
    # 2. RBI Fixed Deposits & DICGC Insurance
    {
        "id": "eval-rbi-01",
        "category": "rbi_banking",
        "query": "How much deposit insurance protection does DICGC provide for bank fixed deposits in India?",
        "expected_organization": "RBI",
        "expected_topic": "fixed_income",
        "expected_keywords": ["5,00,000", "DICGC", "five lakhs"],
        "is_out_of_domain": False,
        "requires_multi_chunk": False,
    },
    # 3. CBDT Capital Gains Taxation
    {
        "id": "eval-cbdt-01",
        "category": "cbdt_taxation",
        "query": "What are the LTCG and STCG tax rates on equity mutual funds under Finance Act 2024?",
        "expected_organization": "CBDT",
        "expected_topic": "taxation",
        "expected_keywords": ["12.5%", "20%", "1,25,000"],
        "is_out_of_domain": False,
        "requires_multi_chunk": False,
    },
    # 4. PFRDA National Pension System (NPS)
    {
        "id": "eval-pfrda-01",
        "category": "pfrda_retirement",
        "query": "What is the exclusive additional tax deduction limit for NPS Tier 1 under Section 80CCD(1B)?",
        "expected_organization": "PFRDA",
        "expected_topic": "retirement",
        "expected_keywords": ["80CCD(1B)", "50,000", "2,00,000"],
        "is_out_of_domain": False,
        "requires_multi_chunk": False,
    },
    # 5. RBI Sovereign Gold Bonds (SGB)
    {
        "id": "eval-sgb-01",
        "category": "rbi_gold",
        "query": "What is the annual coupon interest rate on Sovereign Gold Bonds and is maturity capital gain tax exempt?",
        "expected_organization": "RBI",
        "expected_topic": "gold_investments",
        "expected_keywords": ["2.50%", "exempt", "8 years"],
        "is_out_of_domain": False,
        "requires_multi_chunk": False,
    },
    # 6. Multi-Chunk Synthesis (Asset Allocation & Tax / Product Rules)
    {
        "id": "eval-multi-01",
        "category": "multi_chunk",
        "query": "Compare the taxation and lock-in period between ELSS mutual funds and NPS Tier 1 in India.",
        "expected_organization": None,
        "expected_topic": None,
        "expected_keywords": ["3-year", "80C", "80CCD(1B)", "annuity", "60"],
        "is_out_of_domain": False,
        "requires_multi_chunk": True,
    },
    # 7. Irrelevant / Out-of-Domain Abstention Queries
    {
        "id": "eval-ood-01",
        "category": "out_of_domain",
        "query": "What is the top secret formula for Coca Cola and how do you brew beer at home?",
        "expected_organization": None,
        "expected_topic": None,
        "expected_keywords": [],
        "is_out_of_domain": True,
        "requires_multi_chunk": False,
    },
    {
        "id": "eval-ood-02",
        "category": "out_of_domain",
        "query": "Predict whether the NIFTY stock index will hit 30000 points tomorrow morning.",
        "expected_organization": None,
        "expected_topic": None,
        "expected_keywords": [],
        "is_out_of_domain": True,
        "requires_multi_chunk": False,
    },
]
