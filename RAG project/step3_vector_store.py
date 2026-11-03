import os
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

# Import functions from previous steps
from step1_loader import load_files_from_folder
from step2_chunking import split_documents_into_chunks

# Directory where ChromaDB will persist its SQLite and vector files
DB_DIRECTORY = "./chroma_db"
COLLECTION_NAME = "local_rag_collection"

# 1. Initialize the local embedding model running in Ollama
print("Connecting to local embedding model...")
embeddings = OllamaEmbeddings(model="nomic-embed-text")


def build_and_save_vector_store():
    # Load and chunk files
    raw_docs = load_files_from_folder("./data")
    if not raw_docs:
        print("No documents found in ./data to index.")
        return None

    chunks = split_documents_into_chunks(raw_docs, chunk_size=500, chunk_overlap=50)
    print(f"Embedding and indexing {len(chunks)} chunks into ChromaDB...")

    # 2. Chroma.from_documents embeds the chunks and writes them to disk
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=DB_DIRECTORY
    )
    print("Vector database successfully built and saved to disk!\n")
    return vector_store


def load_existing_vector_store():
    """Loads the database from disk without re-embedding everything."""
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=DB_DIRECTORY
    )


if __name__ == "__main__":
    # Check if database already exists on disk
    if not os.path.exists(DB_DIRECTORY):
        vector_db = build_and_save_vector_store()
    else:
        print("Found existing database on disk. Loading without re-embedding...")
        vector_db = load_existing_vector_store()

    if vector_db:
        # 3. Test Retrieval: Similarity Search
        test_query = "What is linear regression?"
        print(f"--- Running a Test Search ---")
        print(f"Query: '{test_query}'\n")

        # Retrieve top 2 most semantically relevant chunks
        results = vector_db.similarity_search_with_score(test_query, k=2)
        print(results)

        for i, (doc, score) in enumerate(results, start=1):
            print(f"Result #{i} (Distance Score: {score:.4f})")
            print(f"Source: {doc.metadata.get('source')} | Page: {doc.metadata.get('page', 'N/A')}")
            print(f"Content:\n{doc.page_content.strip()}")
            print("-" * 50)