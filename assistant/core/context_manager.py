"""
AskSharon.ai Context Manager
============================
Unified memory API (SQLite structured memory + FAISS semantic index).
"""

from sqlalchemy import create_engine, text
import faiss
import numpy as np

DB_PATH = "assistant/data/memory.db"
engine = create_engine(f"sqlite:///{DB_PATH}")

# Placeholder 128-dim index; replace with real embeddings later
faiss_index = faiss.IndexFlatL2(128)


def recall(query_vector, top_k=5):
    """Return top_k similar memory entries (stub)."""
    if faiss_index.ntotal == 0:
        return []
    distances, ids = faiss_index.search(np.array([query_vector]).astype("float32"), top_k)
    with engine.connect() as conn:
        results = conn.execute(
            text("SELECT * FROM memory WHERE id IN :ids"), {"ids": tuple(ids[0])}
        )
    return results.fetchall()


def store(text_entry, vector):
    """Store text and vector (semantic memory)."""
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO memory (content) VALUES (:c)"), {"c": text_entry})
    faiss_index.add(np.array([vector]).astype("float32"))
    print(f"🧠 Stored memory: {text_entry[:60]}...")
