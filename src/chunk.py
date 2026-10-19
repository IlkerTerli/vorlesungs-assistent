"""Schritt 8: Transkript in größere Abschnitte (Chunks) zerlegen.

Beispiel:
    python src/chunk.py data/transcripts/b68PKSQwgtE.small.json
"""
import argparse
import json
from pathlib import Path

OUT_DIR = Path("data/chunks")
RAW_DIR = Path("data/raw")


def fmt(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def make_chunks(segments: list[dict], window_s: float, overlap_s: float) -> list[dict]:
    """Fasst kurze Segmente zu Abschnitten von ca. window_s Sekunden zusammen.
    Aufeinanderfolgende Abschnitte überlappen um ca. overlap_s Sekunden,
    damit kein Gedanke genau an einer Schnittstelle zerrissen wird."""
    chunks = []
    i = 0
    while i < len(segments):
        start = segments[i]["start"]
        group = []
        j = i
        while j < len(segments):
            group.append(segments[j])
            j += 1
            if group[-1]["end"] - start >= window_s:
                break

        chunks.append({
            "chunk_id": len(chunks),
            "start": group[0]["start"],
            "end": group[-1]["end"],
            "text": " ".join(s["text"] for s in group),
        })
        if j >= len(segments):
            break

        # Nächster Abschnitt beginnt ein Stück vor dem Ende des aktuellen
        next_i = j
        while next_i > i + 1 and segments[next_i - 1]["start"] > group[-1]["end"] - overlap_s:
            next_i -= 1
        i = next_i
    return chunks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transkript in Abschnitte zerlegen")
    parser.add_argument("transcript", help="Pfad zur Transkript-JSON in data/transcripts")
    parser.add_argument("--window", type=float, default=60, help="Länge eines Abschnitts in Sekunden")
    parser.add_argument("--overlap", type=float, default=10, help="Überlappung in Sekunden")
    args = parser.parse_args()

    path = Path(args.transcript)
    data = json.loads(path.read_text(encoding="utf-8"))
    video_id = path.name.split(".")[0]

    meta_path = RAW_DIR / f"{video_id}.meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}

    chunks = make_chunks(data["segments"], args.window, args.overlap)
    for c in chunks:
        c["video_id"] = video_id
        c["title"] = meta.get("title")
        c["url"] = meta.get("url")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{video_id}.chunks.json"
    out.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{len(data['segments'])} Segmente -> {len(chunks)} Abschnitte")
    print(f"Gespeichert: {out}\n")
    for c in chunks[:2]:
        print(f"--- Abschnitt {c['chunk_id']} [{fmt(c['start'])} - {fmt(c['end'])}] ---")
        print(c["text"][:300] + ("..." if len(c["text"]) > 300 else ""), "\n")