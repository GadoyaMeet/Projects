import os
from pathlib import Path
from typing import List
from pypdf import PdfReader
from docx import Document as DocxReader
from langchain_core.documents import Document


# --- 1. Individual File Readers ---

def read_txt(file_path: Path) -> List[Document]:
    """Reads a plain text file into a single Document."""
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    if not text.strip():
        return []
    
    return [
        Document(
            page_content=text,
            metadata={"source": file_path.name, "file_type": "txt"}
        )
    ]


def read_pdf(file_path: Path) -> List[Document]:
    """Reads a PDF page-by-page, creating one Document per page."""
    docs = []
    reader = PdfReader(str(file_path))
    
    for page_idx, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            docs.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": file_path.name,
                        "file_type": "pdf",
                        "page": page_idx
                    }
                )
            )
    return docs


def read_docx(file_path: Path) -> List[Document]:
    """Reads a Word document into a single Document."""
    doc = DocxReader(str(file_path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    text = "\n\n".join(paragraphs)
    
    if not text.strip():
        return []
    
    return [
        Document(
            page_content=text,
            metadata={"source": file_path.name, "file_type": "docx"}
        )
    ]


# --- 2. Folder Scanner ---

def load_files_from_folder(folder_path: str) -> List[Document]:
    """Scans the folder and dispatches each file to its corresponding reader."""
    folder = Path(folder_path)
    
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Folder '{folder_path}' does not exist.")

    loaded_documents: List[Document] = []

    for file_path in folder.iterdir():
        if not file_path.is_file():
            continue

        ext = file_path.suffix.lower()

        if ext == ".txt":
            docs = read_txt(file_path)
        elif ext == ".pdf":
            docs = read_pdf(file_path)
        elif ext == ".docx":
            docs = read_docx(file_path)
        else:
            print(f"Skipping unsupported file: {file_path.name}")
            continue

        print(f"Loaded '{file_path.name}' -> {len(docs)} Document object(s)")
        loaded_documents.extend(docs)

    return loaded_documents


# --- 3. Run and Inspect ---

if __name__ == "__main__":
    folder_name = "./data"
    os.makedirs(folder_name, exist_ok=True)

    print(f"Reading files from: {folder_name}/\n")
    all_docs = load_files_from_folder(folder_name)

    print(f"\nTotal Document objects loaded in memory: {len(all_docs)}")

    # Inspect what a Document object looks like in memory
    if all_docs:
        print("\n--- Inspecting the First Loaded Document ---")
        first = all_docs[0]
        print(f"Metadata: {first.metadata}")
        print(f"Character count: {len(first.page_content)}")
        print(f"Preview (first 150 characters):\n{first.page_content[:150]}...")