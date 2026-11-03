from langchain_chroma import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

DB_DIRECTORY = "./chroma_db"
COLLECTION_NAME = "local_rag_collection"

# 1. Connect to the local models running in Ollama
embeddings = OllamaEmbeddings(model="nomic-embed-text")
llm = ChatOllama(model="qwen2.5:3b", temperature=0)

# 2. Load the existing ChromaDB vector store
vector_store = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=embeddings,
    persist_directory=DB_DIRECTORY
)

# 3. Configure the retriever (fetch top 3 chunks)
retriever = vector_store.as_retriever(search_kwargs={"k": 3})

# 4. Define the prompt template
prompt = ChatPromptTemplate.from_template(
    """Answer the question based strictly on the provided context below.
If the answer is not contained in the context, say "I cannot find this information in the document."

Context:
{context}

Question: {question}

Answer:"""
)

# Helper function to format retrieved chunks into a single context string
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# 5. Build the LCEL Chain
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# 6. Ask the question
if __name__ == "__main__":
    query = "What is this pdf all about?"
    print(f"Question: {query}\n")
    print("Generating answer with Qwen2.5-3B...")
    
    response = rag_chain.invoke(query)
    
    print("\n--- Final Generated Answer ---")
    print(response)