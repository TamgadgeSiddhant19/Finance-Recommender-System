import re
from typing import Dict, List, Tuple
from app.rag.schemas import QueryIntentEnum, QueryRouteResult


class QueryRouter:
    """
    RAG 2.0 Deterministic Query Intent Router.
    Routes user prompts to appropriate specialized engines without LLM ambiguity.
    """

    # Keyword patterns for each deterministic intent
    MARKET_DATA_PATTERNS = [
        r"\b(stock price|share price|market price|ticker|quote|nav|pe ratio|52 week|market cap of)\b",
        r"\b(price of|current price|trading at|nifty|sensex|banknifty|bse|nse)\b",
        r"\b(reliance|tcs|infosys|hdfc bank|icici bank|itc|tata motors)\s+(price|share|stock)\b",
    ]

    DETERMINISTIC_FINANCE_PATTERNS = [
        r"\b(how much sip|calculate sip|sip calculator|sip required|sip needed)\b",
        r"\b(goal projection|calculate returns|future value|monthly capacity|surplus calculation)\b",
        r"\b(how much (can|should) i invest|target corpus|accumulate \d+|reach \d+ (lakh|crore))\b",
        r"\b(calculate|compute|project)\s+(corpus|fv|future value|retirement fund)\b",
    ]

    RECOMMENDATION_EXPLANATION_PATTERNS = [
        r"\b(why did artha recommend|why was .* recommended|why this fund|why this allocation)\b",
        r"\b(explain my recommendation|decision trace|why .* equity|why .* debt|why excluded)\b",
        r"\b(audit trail|recommendation rationale|why not invest in)\b",
    ]

    KNOWLEDGE_PATTERNS = [
        r"\b(what is|how does|what are the rules|guidelines|circular|mandate|definition of)\b",
        r"\b(taxation|tax slab|ltcg|stcg|capital gains|section 112a|section 80c|section 80ccd|dicgc)\b",
        r"\b(mutual fund|large cap|mid cap|small cap|flexi cap|liquid fund|sgb|sovereign gold bond|nps|fixed deposit)\b",
        r"\b(sebi|rbi|cbdt|pfrda|amfi|irdai)\b",
    ]

    @classmethod
    def route_query(cls, query: str) -> QueryRouteResult:
        """
        Classify user query deterministically into one of the four domain intents.
        """
        clean_q = query.strip().lower()

        # 1. Check Recommendation Explanation Intent
        for pat in cls.RECOMMENDATION_EXPLANATION_PATTERNS:
            if re.search(pat, clean_q, re.IGNORECASE):
                return QueryRouteResult(
                    query=query,
                    intent=QueryIntentEnum.RECOMMENDATION_EXPLANATION,
                    confidence=0.95,
                    recommended_engine="RecommendationAuditService",
                    reasoning="Query requests explainability or decision trace of generated portfolio recommendations.",
                )

        # 2. Check Live Market Data Intent
        for pat in cls.MARKET_DATA_PATTERNS:
            if re.search(pat, clean_q, re.IGNORECASE):
                return QueryRouteResult(
                    query=query,
                    intent=QueryIntentEnum.MARKET_DATA,
                    confidence=0.90,
                    recommended_engine="MarketDataService",
                    reasoning="Query asks for ticker, equity quote, or real-time index price.",
                )

        # 3. Check Deterministic Calculation / SIP Math Intent
        for pat in cls.DETERMINISTIC_FINANCE_PATTERNS:
            if re.search(pat, clean_q, re.IGNORECASE):
                return QueryRouteResult(
                    query=query,
                    intent=QueryIntentEnum.DETERMINISTIC_FINANCE,
                    confidence=0.92,
                    recommended_engine="GoalProjectionEngine",
                    reasoning="Query asks for mathematical investment calculations, compounding projections, or SIP required.",
                )

        # 4. Check Financial Knowledge / Regulatory RAG Intent
        matched_knowledge = sum(1 for pat in cls.KNOWLEDGE_PATTERNS if re.search(pat, clean_q, re.IGNORECASE))
        if matched_knowledge > 0:
            return QueryRouteResult(
                query=query,
                intent=QueryIntentEnum.KNOWLEDGE,
                confidence=min(1.0, 0.70 + 0.10 * matched_knowledge),
                recommended_engine="RAGService2.0",
                reasoning="Query asks about statutory regulations, financial definitions, tax laws, or institutional frameworks.",
            )

        # Default fallback to RAG 2.0 Knowledge Engine with lower baseline confidence
        return QueryRouteResult(
            query=query,
            intent=QueryIntentEnum.KNOWLEDGE,
            confidence=0.60,
            recommended_engine="RAGService2.0",
            reasoning="Default general financial knowledge inquiry.",
        )
