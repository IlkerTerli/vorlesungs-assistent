"""Schritt 12: Die Vektordatenbank mit einer Frage durchsuchen.

Beispiel:
    python src/search.py "Was ist eine Menge?"
"""
import argparse

from index import get_collection, load_model


def fmt(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def search(question: str, k: int = 3, model=None) -> list[dict]:
    """Findet die k Abschnitte, die inhaltlich am besten zur Frage passen."""
    model = model or load_model()
    # Das e5-Modell erwartet den Vorsatz "query: " vor Suchanfragen
    query_emb = model.encode(["query: " + question], normalize_embeddings=True)
    res = get_collection().query(query_embeddings=query_emb.tolist(), n_results=k)

    hits = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        hits.append({"text": doc, "score": 1 - dist, **meta})
    return hits


def video_link(hit: dict) -> str:
    """Link, der direkt an die Fundstelle im Video springt."""
    if not hit.get("url"):
        return ""
    sep = "&" if "?" in hit["url"] else "?"
    return f"{hit['url']}{sep}t={int(hit['start'])}s"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vorlesungen durchsuchen")
    parser.add_argument("question", help="Deine Frage in Anführungszeichen")
    parser.add_argument("-k", type=int, default=3, help="Anzahl der Treffer")
    args = parser.parse_args()

    for rank, hit in enumerate(search(args.question, args.k), start=1):
        print(f"\n#{rank}  [{fmt(hit['start'])} - {fmt(hit['end'])}]  Ähnlichkeit: {hit['score']:.2f}")
        print(f"    {video_link(hit)}")
        print(f"    {hit['text'][:250]}...")