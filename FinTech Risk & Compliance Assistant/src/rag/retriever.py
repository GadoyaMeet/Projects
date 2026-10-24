"""
Hybrid Search Retriever combining BM25 Lexical Matching and Dense Vector Similarity.
Implements Reciprocal Rank Fusion (RRF) to merge keyword precision with semantic meaning.
Addresses Interview Questions: R1 Q1, R2 Q3 (Improving retrieval accuracy).
"""

from typing import List, Dict, Any, Tuple
import numpy as np
from rank_bm25 import BM25Okapi
from src.rag.chunker import Chunk
from src.rag.embeddings import SemanticDenseEmbedder


class HybridRetriever:
    """
    Dual-index search engine maintaining:
    1. BM25 inverted index for exact financial numbers, clauses, and entity names.
    2. Dense vector index for conceptual semantic similarity.
    Merged via Reciprocal Rank Fusion (RRF, k=60).
    """

    def __init__(self, chunks: List[Chunk]):
        self.chunks = chunks
        self.embedder = SemanticDenseEmbedder(dimension=384)

        # 1. Initialize BM25 Index
        self.tokenized_corpus = [c.text.lower().split() for c in chunks]
        self.bm25 = BM25Okapi(self.tokenized_corpus)

        # 2. Build Dense Vector Index
        self.chunk_vectors = self.embedder.encode([c.text for c in chunks])

    def search(
        self,
        query: str,
        top_k: int = 5,
        dense_weight: float = 0.5,
        borrower_filter: str = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid search combining BM25 and Dense vectors with RRF scoring.
        """
        if not self.chunks:
            return []

        # Filter indices if borrower_filter is provided
        eligible_indices = [
            i for i, c in enumerate(self.chunks)
            if borrower_filter is None or c.metadata.get("borrower_id") == borrower_filter
        ]
        if not eligible_indices:
            eligible_indices = list(range(len(self.chunks)))

        # 1. BM25 Scores & Ranking
        query_tokens = query.lower().split()
        bm25_raw_scores = self.bm25.get_scores(query_tokens)
        bm25_ranked = sorted(eligible_indices, key=lambda idx: bm25_raw_scores[idx], reverse=True)
        bm25_rank_map = {idx: rank for rank, idx in enumerate(bm25_ranked, start=1)}

        # 2. Dense Vector Scores & Ranking
        query_vec = self.embedder.encode(query)
        dense_scores = np.dot(self.chunk_vectors, query_vec)
        dense_ranked = sorted(eligible_indices, key=lambda idx: dense_scores[idx], reverse=True)
        dense_rank_map = {idx: rank for rank, idx in enumerate(dense_ranked, start=1)}

        # 3. Reciprocal Rank Fusion (RRF)
        # Formula: RRF_score(d) = sum(1 / (k + rank_i))
        K = 60
        fused_results: List[Tuple[int, float]] = []

        for idx in eligible_indices:
            r_bm25 = bm25_rank_map.get(idx, 999)
            r_dense = dense_rank_map.get(idx, 999)

            score_bm25 = 1.0 / (K + r_bm25)
            score_dense = 1.0 / (K + r_dense)
            rrf_score = (1 - dense_weight) * score_bm25 + dense_weight * score_dense
            fused_results.append((idx, rrf_score))

        # Sort by RRF score descending
        fused_results.sort(key=lambda x: x[1], reverse=True)

        # Return top_k enriched candidate records
        top_candidates = []
        for idx, rrf_score in fused_results[:top_k]:
            c = self.chunks[idx]
            top_candidates.append({
                "chunk_id": c.chunk_id,
                "parent_id": c.parent_id,
                "text": c.text,
                "parent_text": c.parent_text,
                "is_table": c.is_table,
                "metadata": c.metadata,
                "bm25_rank": bm25_rank_map.get(idx),
                "dense_rank": dense_rank_map.get(idx),
                "bm25_raw_score": round(float(bm25_raw_scores[idx]), 3),
                "dense_cosine_score": round(float(dense_scores[idx]), 3),
                "rrf_score": round(rrf_score, 5),
            })

        return top_candidates
