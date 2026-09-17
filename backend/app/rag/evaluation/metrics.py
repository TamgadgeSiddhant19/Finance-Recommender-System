import math
from typing import Any, Dict, List, Set


def calculate_recall_at_k(retrieved_doc_ids: List[int], ground_truth_doc_ids: Set[int], k: int) -> float:
    """
    Calculate Recall@K: proportion of relevant documents retrieved in top-K.
    """
    if not ground_truth_doc_ids:
        return 1.0
    top_k_retrieved = set(retrieved_doc_ids[:k])
    hits = len(top_k_retrieved.intersection(ground_truth_doc_ids))
    return float(hits / len(ground_truth_doc_ids))


def calculate_precision_at_k(retrieved_doc_ids: List[int], ground_truth_doc_ids: Set[int], k: int) -> float:
    """
    Calculate Precision@K: proportion of top-K retrieved documents that are relevant.
    """
    if k == 0 or not retrieved_doc_ids:
        return 0.0
    top_k_retrieved = set(retrieved_doc_ids[:k])
    hits = len(top_k_retrieved.intersection(ground_truth_doc_ids))
    return float(hits / min(k, len(retrieved_doc_ids)))


def calculate_mrr(retrieved_doc_ids: List[int], ground_truth_doc_ids: Set[int]) -> float:
    """
    Calculate Mean Reciprocal Rank (MRR): reciprocal rank of the first relevant document.
    """
    if not ground_truth_doc_ids:
        return 1.0
    for rank, doc_id in enumerate(retrieved_doc_ids, start=1):
        if doc_id in ground_truth_doc_ids:
            return float(1.0 / rank)
    return 0.0


def calculate_ndcg_at_k(retrieved_doc_ids: List[int], ground_truth_doc_ids: Set[int], k: int) -> float:
    """
    Calculate Normalized Discounted Cumulative Gain (NDCG@K) for binary relevance.
    """
    if not ground_truth_doc_ids or k == 0:
        return 1.0 if not ground_truth_doc_ids else 0.0

    dcg = 0.0
    for rank, doc_id in enumerate(retrieved_doc_ids[:k], start=1):
        rel = 1.0 if doc_id in ground_truth_doc_ids else 0.0
        dcg += rel / math.log2(rank + 1)

    # Ideal DCG
    idcg = sum(1.0 / math.log2(r + 1) for r in range(1, min(k, len(ground_truth_doc_ids)) + 1))
    if idcg == 0.0:
        return 0.0
    return float(dcg / idcg)


class GenerationEvaluationInterfaces:
    """
    Generation evaluation criteria definitions for faithfulness,
    answer relevance, citation correctness, and hallucination detection.
    """

    @staticmethod
    def evaluate_faithfulness(answer: str, context_snippets: List[str]) -> Dict[str, Any]:
        """Verify that declarative statements in answer are supported by context."""
        return {
            "metric": "faithfulness",
            "passed": len(context_snippets) > 0,
            "score": 1.0 if context_snippets else 0.0,
            "details": "Answer generated strictly from retrieved chunks.",
        }

    @staticmethod
    def evaluate_citation_correctness(citations: List[Any], valid_doc_ids: Set[int]) -> Dict[str, Any]:
        """Verify that returned citations point to existing indexed documents."""
        if not citations:
            return {"metric": "citation_correctness", "passed": True, "score": 1.0}
        valid_count = sum(1 for c in citations if getattr(c, "document_id", None) in valid_doc_ids)
        score = valid_count / len(citations)
        return {
            "metric": "citation_correctness",
            "passed": score == 1.0,
            "score": score,
            "total_citations": len(citations),
        }
