from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Import the loader function from your Step 1 code
from step1_loader import load_files_from_folder


def split_documents_into_chunks(
    documents: List[Document],
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[Document]:
    """
    Splits a list of Document objects into smaller chunks.
    
    Args:
        documents: Raw documents from Step 1.
        chunk_size: Target maximum characters per chunk.
        chunk_overlap: Overlapping characters between consecutive chunks.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        # Tries splitting by paragraphs first, then lines, then words, then characters
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = splitter.split_documents(documents)
    return chunks


if __name__ == "__main__":
    folder_path = "./data"
    
    # 1. Load documents (Step 1)
    print("--- 1. Loading Documents ---")
    raw_docs = load_files_from_folder(folder_path)
    
    if not raw_docs:
        print("No documents found in './data'. Please add some files first.")
        exit()
        
    print(f"Total raw Document units loaded: {len(raw_docs)}\n")

    # 2. Split documents into chunks (Step 2)
    print("--- 2. Chunking Documents ---")
    chunks = split_documents_into_chunks(
        documents=raw_docs,
        chunk_size=1000,   # ~100 to 125 words per chunk
        chunk_overlap=150  # ~10 to 12 words overlap to maintain context
    )
    
    print(f"Total chunks created: {len(chunks)}\n")
    # print("chunks created:", chunks)

    # 3. Inspect the first 2 chunks
    print("--- 3. Inspecting Chunks ---")
    for i, chunk in enumerate(chunks[:2]):
        print(f"Chunk #{i + 1}")
        print(f"Source Metadata: {chunk.metadata}")
        print(f"Character Count: {len(chunk.page_content)}")
        print("Content:")
        print(chunk.page_content.strip())
        print("-" * 50)