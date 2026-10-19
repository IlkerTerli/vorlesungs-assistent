"""Schritt 11: Abschnitte als Embeddings in die Vektordatenbank schreiben.

Beispiel:
    python src/index.py data/chunks/b68PKSQwgtE.chunks.json
"""
import argparse
import json
import time
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

DB_DIR = "data/chroma"
COLLECTION = "vorlesungen"
MODEL_NAME = "intfloat/multilingual-e5-small"


def get_collection():
    """Öffnet die Datenbank (oder legt sie beim ersten Mal an)."""
    client = chromadb.PersistentClient(path=DB_DIR)
    return client.get_or_create_collection(
        name=COLLECTION, metadata={"hnsw:space": "cosine"}
    )


def load_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Abschnitte in die Vektordatenbank schreiben")
    parser.add_argument("chunks", help="Pfad zur Chunks-JSON in data/chunks")
    args = parser.parse_args()

    chunks = json.loads(Path(args.chunks).read_text(encoding="utf-8"))
    print(f"{len(chunks)} Abschnitte geladen, lade Embedding-Modell ...")
    model = load_model()

    # Das e5-Modell erwartet den Vorsatz "passage: " vor zu durchsuchenden Texten
    start = time.time()
    embeddings = model.encode(
        ["passage: " + c["text"] for c in chunks],
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    collection = get_collection()
    collection.upsert(
        ids=[f"{c['video_id']}-{c['chunk_id']}" for c in chunks],
        documents=[c["text"] for c in chunks],
        embeddings=embeddings.tolist(),
        metadatas=[
            {
                "video_id": c["video_id"],
                "chunk_id": c["chunk_id"],
                "start": c["start"],
                "end": c["end"],
                "title": c.get("title") or "",
                "url": c.get("url") or "",
            }
            for c in chunks
        ],
    )

    print(f"\nFertig in {time.time() - start:.1f} s")
    print(f"Vektorlänge: {len(embeddings[0])} Zahlen pro Abschnitt")
    print(f"Abschnitte in der Datenbank: {collection.count()}")