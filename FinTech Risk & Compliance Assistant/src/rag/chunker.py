"""
Hierarchical Parent-Child Chunking Strategy.
Addresses Interview Question: R1 Q1 (Chunking strategies for financial filings).
"""

from typing import List, Dict, Any, Optional
import re


class Chunk:
    """Represents a retrievable unit with hierarchical link to its parent section."""

    def __init__(
        self,
        chunk_id: str,
        parent_id: str,
        text: str,
        parent_text: str,
        is_table: bool,
        metadata: Dict[str, Any],
    ):
        self.chunk_id = chunk_id
        self.parent_id = parent_id
        self.text = text
        self.parent_text = parent_text
        self.is_table = is_table
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "parent_id": self.parent_id,
            "text": self.text,
            "parent_text": self.parent_text,
            "is_table": self.is_table,
            "metadata": self.metadata,
        }


class HierarchicalChunker:
    """
    Splits documents into granular child chunks for high-precision vector/BM25 retrieval,
    while maintaining the full parent section to pass rich contextual boundaries to the LLM.
    Preserves financial tables intact without splitting rows.
    """

    def __init__(self, target_child_size: int = 350, child_overlap: int = 50):
        self.target_child_size = target_child_size
        self.child_overlap = child_overlap

    def chunk_document(self, parsed_doc: Dict[str, Any], borrower_id: Optional[str] = None) -> List[Chunk]:
        """
        Takes the output of CorporateReportParser and generates hierarchical chunks.
        """
        chunks: List[Chunk] = []
        doc_title = parsed_doc.get("document_title", "Corporate Filing")
        file_path = parsed_doc.get("file_path", "")

        for s_idx, sec in enumerate(parsed_doc.get("sections", [])):
            parent_id = f"{doc_title[:10]}_sec_{s_idx}"
            parent_text = sec["content"]
            section_title = sec["title"]

            # 1. First extract any markdown tables in this section and preserve each as an atomic chunk
            tables = sec.get("tables", [])
            for t_idx, tbl in enumerate(tables):
                t_chunk_id = f"{parent_id}_tbl_{t_idx}"
                chunks.append(
                    Chunk(
                        chunk_id=t_chunk_id,
                        parent_id=parent_id,
                        text=f"Financial Table from {section_title}:\n{tbl}",
                        parent_text=parent_text,
                        is_table=True,
                        metadata={
                            "document_title": doc_title,
                            "section_title": section_title,
                            "source_file": file_path,
                            "borrower_id": borrower_id,
                            "type": "table",
                        },
                    )
                )

            # 2. Chunk narrative prose by paragraphs or sentences
            # Remove tables from narrative text to avoid redundant splitting
            narrative = parent_text
            for tbl in tables:
                narrative = narrative.replace(tbl, "")

            paragraphs = [p.strip() for p in narrative.split("\n\n") if p.strip()]
            child_idx = 0

            for para in paragraphs:
                if len(para) <= self.target_child_size:
                    c_id = f"{parent_id}_child_{child_idx}"
                    chunks.append(
                        Chunk(
                            chunk_id=c_id,
                            parent_id=parent_id,
                            text=para,
                            parent_text=parent_text,
                            is_table=False,
                            metadata={
                                "document_title": doc_title,
                                "section_title": section_title,
                                "source_file": file_path,
                                "borrower_id": borrower_id,
                                "type": "prose",
                            },
                        )
                    )
                    child_idx += 1
                else:
                    # Split longer paragraphs into overlapping sentence windows
                    sentences = re.split(r"(?<=[.!?])\s+", para)
                    curr_child = []
                    curr_len = 0

                    for sent in sentences:
                        curr_child.append(sent)
                        curr_len += len(sent)
                        if curr_len >= self.target_child_size:
                            chunk_str = " ".join(curr_child)
                            c_id = f"{parent_id}_child_{child_idx}"
                            chunks.append(
                                Chunk(
                                    chunk_id=c_id,
                                    parent_id=parent_id,
                                    text=chunk_str,
                                    parent_text=parent_text,
                                    is_table=False,
                                    metadata={
                                        "document_title": doc_title,
                                        "section_title": section_title,
                                        "source_file": file_path,
                                        "borrower_id": borrower_id,
                                        "type": "prose",
                                    },
                                )
                            )
                            child_idx += 1
                            curr_child = curr_child[-1:]  # Overlap 1 sentence
                            curr_len = sum(len(s) for s in curr_child)

                    if curr_child and len(" ".join(curr_child)) > 30:
                        c_id = f"{parent_id}_child_{child_idx}"
                        chunks.append(
                            Chunk(
                                chunk_id=c_id,
                                parent_id=parent_id,
                                text=" ".join(curr_child),
                                parent_text=parent_text,
                                is_table=False,
                                metadata={
                                    "document_title": doc_title,
                                    "section_title": section_title,
                                    "source_file": file_path,
                                    "borrower_id": borrower_id,
                                    "type": "prose",
                                },
                            )
                        )
                        child_idx += 1

        return chunks
