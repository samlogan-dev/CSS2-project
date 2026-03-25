"""
ingest.py — Load, chunk, embed, and store docs in ChromaDB.

Usage:
    python ingest.py
    python main.py ingest

Clears and rebuilds the collection on each run (idempotent).
"""

import os
import glob

import chromadb
from sentence_transformers import SentenceTransformer

DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
COLLECTION_NAME = "knowledge_base"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

EMBED_MODEL = "all-MiniLM-L6-v2"


def load_documents(docs_dir: str) -> list[dict]:
    """Load all .md files from docs_dir, return list of {source, text} dicts."""
    docs = []
    paths = sorted(glob.glob(os.path.join(docs_dir, "*.md")))
    if not paths:
        raise FileNotFoundError(f"No .md files found in {docs_dir}")
    for path in paths:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        docs.append({"source": os.path.basename(path), "text": text})
    return docs


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Recursive character splitter: split on double newline, then single newline,
    then space, falling back to hard character splits.
    """
    separators = ["\n\n", "\n", " ", ""]

    def _split(text: str, seps: list[str]) -> list[str]:
        if not seps or len(text) <= chunk_size:
            return [text] if text.strip() else []

        sep = seps[0]
        parts = text.split(sep) if sep else list(text)

        chunks = []
        current = ""
        for part in parts:
            candidate = current + (sep if current else "") + part
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current.strip():
                    chunks.extend(_split(current, seps[1:]))
                current = part
        if current.strip():
            chunks.extend(_split(current, seps[1:]))

        return chunks

    raw_chunks = _split(text, separators)

    # Apply overlap: each chunk includes a tail of the previous chunk
    if overlap <= 0 or len(raw_chunks) <= 1:
        return raw_chunks

    overlapped = [raw_chunks[0]]
    for i in range(1, len(raw_chunks)):
        tail = overlapped[-1][-overlap:]
        overlapped.append(tail + raw_chunks[i])

    return overlapped


def ingest(docs_dir: str = DOCS_DIR, chroma_dir: str = CHROMA_DIR) -> None:
    print(f"Loading documents from {docs_dir} ...")
    docs = load_documents(docs_dir)
    print(f"  Loaded {len(docs)} documents.")

    # Build chunks with metadata
    all_chunks = []
    for doc in docs:
        chunks = chunk_text(doc["text"])
        for idx, chunk in enumerate(chunks):
            all_chunks.append({
                "text": chunk,
                "source": doc["source"],
                "chunk_index": idx,
                "id": f"{doc['source']}::chunk{idx}",
            })

    print(f"  Split into {len(all_chunks)} chunks.")

    # Embed
    print(f"Loading embedding model '{EMBED_MODEL}' ...")
    model = SentenceTransformer(EMBED_MODEL)
    texts = [c["text"] for c in all_chunks]
    print(f"  Embedding {len(texts)} chunks ...")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=64)

    # Store in ChromaDB
    print(f"Storing in ChromaDB at {chroma_dir} ...")
    client = chromadb.PersistentClient(path=chroma_dir)

    # Idempotent: delete and recreate the collection
    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        client.delete_collection(COLLECTION_NAME)
        print(f"  Deleted existing collection '{COLLECTION_NAME}'.")

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    collection.add(
        ids=[c["id"] for c in all_chunks],
        embeddings=embeddings.tolist(),
        documents=texts,
        metadatas=[{"source": c["source"], "chunk_index": c["chunk_index"]} for c in all_chunks],
    )

    print(f"  Stored {len(all_chunks)} chunks in collection '{COLLECTION_NAME}'.")
    print("Ingestion complete.")


if __name__ == "__main__":
    ingest()
