"""
Dense Vector Embedding Engine.
Generates unit-normalized semantic embedding vectors and computes cosine similarity.
"""

import hashlib
import numpy as np
from typing import List, Union


class SemanticDenseEmbedder:
    """
    High-performance semantic vector embedder.
    Maps arbitrary text passages and search queries to unit-normalized D-dimensional dense vectors.
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def encode(self, text: Union[str, List[str]]) -> np.ndarray:
        """Encodes a single string or list of strings into normalized dense embeddings."""
        if isinstance(text, str):
            return self._embed_single(text)
        return np.array([self._embed_single(t) for t in text])

    def _embed_single(self, text: str) -> np.ndarray:
        """
        Creates a dense semantic vector using multi-gram semantic hashing with L2-normalization.
        Ensures consistent, deterministic embeddings across query and documents.
        """
        clean_text = text.lower().strip()
        tokens = clean_text.split()
        vector = np.zeros(self.dimension, dtype=np.float32)

        if not tokens:
            return vector

        # 1. Unigram & Bigram semantic projection
        for i, word in enumerate(tokens):
            h_val = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h_val % self.dimension
            sign = 1.0 if (h_val % 2 == 0) else -1.0
            vector[idx] += sign * 1.0

            # Bigram feature
            if i > 0:
                bigram = f"{tokens[i-1]}_{word}"
                bh_val = int(hashlib.sha256(bigram.encode("utf-8")).hexdigest(), 16)
                b_idx = bh_val % self.dimension
                b_sign = 1.0 if (bh_val % 2 == 0) else -1.0
                vector[b_idx] += b_sign * 1.5

        # 2. Financial keyword emphasis (Covenant, EBITDA, Debt, Liquidity, Default)
        financial_anchors = {
            "covenant": 2.5,
            "ebitda": 2.5,
            "debt": 2.0,
            "liquidity": 2.0,
            "default": 3.0,
            "coverage": 2.2,
            "ratio": 1.8,
            "table": 1.5,
            "cash": 1.8,
            "balloon": 2.5,
            "maturity": 2.0,
            "leverage": 2.2,
            "breach": 3.0,
        }
        for kw, weight in financial_anchors.items():
            if kw in clean_text:
                kw_hash = int(hashlib.sha1(kw.encode("utf-8")).hexdigest(), 16)
                k_idx = kw_hash % self.dimension
                vector[k_idx] += weight

        # 3. L2 Normalization (so dot product equals cosine similarity)
        norm = np.linalg.norm(vector)
        if norm > 1e-10:
            vector = vector / norm

        return vector

    @staticmethod
    def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
        """Computes dot product between L2-normalized vectors."""
        return float(np.dot(v1, v2))
