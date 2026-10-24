"""
Advanced RAG Module for FinTech Risk & Compliance Assistant.
Provides Parent-Child chunking, Hybrid Search (BM25 + Dense Vectors), and Cross-Encoder Reranking.
Addresses Interview Questions:
- R1 Q1: Chunking Strategies (Parent-Child vs Recursive)
- R2 Q3: Improving Retrieval Accuracy with Hybrid Search & Cross-Encoder Reranking
"""

from src.rag.chunker import HierarchicalChunker, Chunk
from src.rag.retriever import HybridRetriever
from src.rag.reranker import CrossEncoderReranker

__all__ = ["HierarchicalChunker", "Chunk", "HybridRetriever", "CrossEncoderReranker"]
