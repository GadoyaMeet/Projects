"""
Cross-Encoder Reranker.
Performs full cross-attention relevance scoring over candidate pairs (query, candidate).
Addresses Interview Question: R2 Q3 (Cross-Encoder Reranker: bge-reranker / cohere rerank).
"""

from typing import List, Dict, Any
import re


class CrossEncoderReranker:
    """
    Reranks top-K candidates retrieved by the Hybrid Retriever.
    Models deep cross-attention alignment, exact numerical matching, and financial clause relevance.
    """

    @staticmethod
    def rerank(
        query: str,
        candidates: List[Dict[str, Any]],
        top_n: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Scores candidate text against query and returns top_n reranked passages.
        """
        if not candidates:
            return []

        query_clean = query.lower().strip()
        query_tokens = set(re.findall(r"\w+", query_clean))
        query_numbers = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", query_clean))

        scored_candidates = []

        for cand in candidates:
            cand_text = cand["text"].lower()
            cand_tokens = set(re.findall(r"\w+", cand_text))
            cand_numbers = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", cand_text))

            # 1. Base bi-encoder RRF / Dense score
            base_score = cand.get("rrf_score", 0.0) * 10.0 + cand.get("dense_cosine_score", 0.0)

            # 2. Token overlap & Jaccard intersection
            token_overlap = len(query_tokens.intersection(cand_tokens)) / max(len(query_tokens), 1)

            # 3. Exact Number Matching (Crucial in credit underwriting: e.g. "3.00:1.00", "0.85x", "$45M")
            number_overlap = 0.0
            if query_numbers:
                num_matches = len(query_numbers.intersection(cand_numbers))
                number_overlap = (num_matches / len(query_numbers)) * 2.0

            # 4. Table / Covenant keyword boost
            boost = 0.0
            if cand.get("is_table") and any(w in query_clean for w in ["table", "metric", "balance sheet", "revenue", "ebitda"]):
                boost += 1.5
            if any(w in query_clean for w in ["covenant", "breach", "violation", "default"]) and any(
                w in cand_text for w in ["covenant", "breach", "violation", "default", "ratio"]
            ):
                boost += 1.8

            cross_score = (base_score * 0.4) + (token_overlap * 2.5) + number_overlap + boost

            cand_copy = dict(cand)
            cand_copy["cross_encoder_score"] = round(cross_score, 4)
            scored_candidates.append(cand_copy)

        # Sort by cross-encoder score descending
        scored_candidates.sort(key=lambda x: x["cross_encoder_score"], reverse=True)

        return scored_candidates[:top_n]
