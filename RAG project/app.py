import io
import json
import os
import shutil
import sqlite3
import uuid
from pathlib import Path
from typing import List, Any, Optional, AsyncGenerator

import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from step1_loader import load_files_from_folder
from step2_chunking import split_documents_into_chunks

app = FastAPI(title="Unified SQLite Local RAG")

SQLITE_DB = "rag_vault.db"
DATA_DIRECTORY = "./data"
os.makedirs(DATA_DIRECTORY, exist_ok=True)

# -------------------------------------------------------------
# 1. Database Initialization
# -------------------------------------------------------------
def get_db():
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_sqlite_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT,
                active_document TEXT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                sender TEXT,
                content TEXT,
                mode TEXT,
                sources_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                page INTEGER,
                content TEXT,
                embedding BLOB
            )
        """)
init_sqlite_db()


# -------------------------------------------------------------
# 2. Local Models Configuration
# -------------------------------------------------------------
embeddings = OllamaEmbeddings(model="nomic-embed-text")
rag_llm = ChatOllama(model="qwen2.5:3b", temperature=0, num_ctx=3072)
chat_llm = ChatOllama(model="qwen2.5:3b", temperature=0.7, num_ctx=3072)

rag_prompt = ChatPromptTemplate.from_template(
    """You are a helpful assistant reading from an attached document and maintaining an ongoing conversation.
Document Context:
{context}

Prior Conversation History:
{chat_history}

Current Question: {question}

Instructions:
1. Use the Document Context to answer facts, names, roles, and details about the document.
2. Use the Prior Conversation History to remember the user's name, preferences, past context, or follow-up details.
3. If the answer cannot be found in either, state that you do not have enough information.

Answer:"""
)

general_prompt = ChatPromptTemplate.from_template(
    """You are a helpful, knowledgeable, and friendly AI assistant.
Prior Conversation History:
{chat_history}

Current Question: {question}

Instructions:
Use the conversation history to remember user details (like names, schedules, or earlier topics) and resolve follow-up questions. Answer naturally and factually.

Answer:"""
)


# -------------------------------------------------------------
# 3. Vector Search & History Helpers
# -------------------------------------------------------------
def search_similar_chunks(query_vector: list, top_k: int = 6, filename: Optional[str] = None):
    with get_db() as conn:
        if filename:
            rows = conn.execute(
                "SELECT id, source, page, content, embedding FROM document_chunks WHERE source = ?",
                (filename,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT id, source, page, content, embedding FROM document_chunks").fetchall()

    if not rows:
        return []

    query_arr = np.array(query_vector, dtype=np.float32)
    chunk_vectors = np.array([np.frombuffer(r["embedding"], dtype=np.float32) for r in rows])

    dot_products = np.dot(chunk_vectors, query_arr)
    norms = np.linalg.norm(chunk_vectors, axis=1) * np.linalg.norm(query_arr)
    similarities = dot_products / np.maximum(norms, 1e-10)

    top_indices = np.argsort(similarities)[::-1][:top_k]
    return [{
        "source": rows[i]["source"],
        "page": rows[i]["page"],
        "content": rows[i]["content"],
        "score": float(similarities[i])
    } for i in top_indices]


def get_recent_history_text(session_id: str, limit: int = 16) -> str:
    """Retains up to 16 recent messages (8 conversational turns) safely within 3072 tokens."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT sender, content FROM messages 
               WHERE session_id = ? 
               ORDER BY id DESC LIMIT ?""",
            (session_id, limit)
        ).fetchall()

    if not rows:
        return "No prior conversation."

    formatted = []
    for r in reversed(rows):
        role = "User" if r["sender"] == "user" else "Assistant"
        formatted.append(f"{role}: {r['content']}")
    return "\n".join(formatted)


# -------------------------------------------------------------
# 4. Schemas
# -------------------------------------------------------------
class QueryRequest(BaseModel):
    session_id: Optional[str] = None
    question: str
    top_k: int = 6
    has_document: bool = False
    filename: Optional[str] = None

class CreateSessionRequest(BaseModel):
    title: Optional[str] = "New Chat"


# -------------------------------------------------------------
# 5. SSE Streaming Generator with Sticky Session Context
# -------------------------------------------------------------
async def generate_rag_stream(payload: QueryRequest) -> AsyncGenerator[str, None]:
    session_id = payload.session_id or "default_session"
    question = payload.question

    with get_db() as conn:
        sess = conn.execute("SELECT id, title, active_document FROM sessions WHERE id = ?", (session_id,)).fetchone()
        
        # If user explicitly attached a file in this prompt, set it as the session's active document
        if payload.has_document and payload.filename:
            active_doc = payload.filename
            if sess:
                conn.execute("UPDATE sessions SET active_document = ? WHERE id = ?", (active_doc, session_id))
        else:
            # Otherwise, inherit the active document already attached to this session
            active_doc = sess["active_document"] if sess else None

        if not sess:
            title = question[:35] + "..." if len(question) > 35 else question
            conn.execute("INSERT INTO sessions (id, title, active_document) VALUES (?, ?, ?)", 
                         (session_id, title, active_doc))
        elif sess["title"] == "New Chat":
            new_title = question[:35] + "..." if len(question) > 35 else question
            conn.execute("UPDATE sessions SET title = ? WHERE id = ?", (new_title, session_id))

    history_text = get_recent_history_text(session_id, limit=16)

    # Save user message
    with get_db() as conn:
        conn.execute("INSERT INTO messages (session_id, sender, content) VALUES (?, 'user', ?)", 
                     (session_id, question))

    full_answer = ""

    # Route 1: Document RAG (active_doc exists in this chat session)
    if active_doc:
        mode = "document"
        query_vector = embeddings.embed_query(question)
        matched_chunks = search_similar_chunks(query_vector, top_k=payload.top_k, filename=active_doc)

        sources = [
            {
                "source": c["source"],
                "page": c["page"],
                "snippet": c["content"][:200].replace("\n", " ") + "..."
            }
            for c in matched_chunks
        ]

        yield f"data: {json.dumps({'type': 'meta', 'mode': mode, 'active_document': active_doc, 'sources': sources})}\n\n"

        context_text = "\n\n".join(c["content"] for c in matched_chunks)
        chain = rag_prompt | rag_llm | StrOutputParser()
        async for chunk in chain.astream({
            "context": context_text,
            "chat_history": history_text,
            "question": question
        }):
            full_answer += chunk
            yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

    # Route 2: Pure General Chat (no document attached to session)
    else:
        mode = "general_knowledge"
        sources = []
        yield f"data: {json.dumps({'type': 'meta', 'mode': mode, 'active_document': None, 'sources': []})}\n\n"

        chain = general_prompt | chat_llm | StrOutputParser()
        async for chunk in chain.astream({"chat_history": history_text, "question": question}):
            full_answer += chunk
            yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

    # Save assistant response
    with get_db() as conn:
        conn.execute(
            """INSERT INTO messages (session_id, sender, content, mode, sources_json) 
               VALUES (?, 'assistant', ?, ?, ?)""",
            (session_id, full_answer, mode, json.dumps(sources))
        )

    yield f"data: {json.dumps({'type': 'done'})}\n\n"


# -------------------------------------------------------------
# 6. Endpoints
# -------------------------------------------------------------
@app.get("/")
def serve_frontend():
    return FileResponse("index.html")

@app.get("/api/stats")
def get_stats():
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM document_chunks").fetchone()[0]
    return {"total_chunks": count}

@app.get("/api/sessions")
def list_sessions():
    with get_db() as conn:
        rows = conn.execute("SELECT id, title, active_document, created_at FROM sessions ORDER BY created_at DESC").fetchall()
        return [{"id": r["id"], "title": r["title"], "active_document": r["active_document"], "created_at": r["created_at"]} for r in rows]

@app.post("/api/sessions")
def create_session(body: CreateSessionRequest):
    new_id = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute("INSERT INTO sessions (id, title) VALUES (?, ?)", (new_id, body.title))
    return {"id": new_id, "title": body.title}

@app.get("/api/sessions/{session_id}/messages")
def get_session_messages(session_id: str):
    with get_db() as conn:
        rows = conn.execute(
            """SELECT id, sender, content, mode, sources_json, created_at 
               FROM messages WHERE session_id = ? ORDER BY id ASC""",
            (session_id,)
        ).fetchall()
        
        messages = []
        for r in rows:
            sources = json.loads(r["sources_json"]) if r["sources_json"] else []
            messages.append({
                "id": r["id"],
                "sender": r["sender"],
                "content": r["content"],
                "mode": r["mode"],
                "sources": sources
            })
        return messages

@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str):
    with get_db() as conn:
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    return {"status": "success", "deleted_session_id": session_id}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    save_path = Path(DATA_DIRECTORY) / file.filename

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    with get_db() as conn:
        conn.execute("DELETE FROM document_chunks WHERE source = ?", (file.filename,))

    raw_docs = load_files_from_folder(DATA_DIRECTORY)
    file_docs = [d for d in raw_docs if d.metadata.get("source") == file.filename]

    if not file_docs:
        raise HTTPException(status_code=400, detail="Could not extract readable text from file.")

    chunks = split_documents_into_chunks(file_docs, chunk_size=1000, chunk_overlap=150)
    texts = [c.page_content for c in chunks]
    chunk_embeddings = embeddings.embed_documents(texts)

    with get_db() as conn:
        for chunk, emb in zip(chunks, chunk_embeddings):
            blob = np.array(emb, dtype=np.float32).tobytes()
            conn.execute(
                """INSERT INTO document_chunks (source, page, content, embedding)
                   VALUES (?, ?, ?, ?)""",
                (file.filename, chunk.metadata.get("page", 1), chunk.page_content, blob)
            )
        total = conn.execute("SELECT COUNT(*) FROM document_chunks").fetchone()[0]

    return {
        "status": "success",
        "filename": file.filename,
        "chunks_indexed": len(chunks),
        "total_chunks": total
    }

@app.post("/api/ask")
async def ask_question(payload: QueryRequest):
    return StreamingResponse(
        generate_rag_stream(payload),
        media_type="text/event-stream"
    )