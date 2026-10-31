"""Schritt 17: Komplette Pipeline – vom Video-Link bis zur durchsuchbaren Vorlesung.

Beispiel:
    python src/pipeline.py "https://www.youtube.com/watch?v=b68PKSQwgtE"
"""
import argparse
import json
import time
from pathlib import Path

from chunk import fmt, make_chunks
from index import index_chunks
from ingest import RAW_DIR, download_audio, import_local
from transcribe import transcribe

TRANSCRIPT_DIR = Path("data/transcripts")
CHUNK_DIR = Path("data/chunks")


def step(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def run(source: str, model_size: str = "small", language: str = "de",
        window: float = 60, overlap: float = 10) -> None:
    timings = {}

    # 1) Audio holen (yt-dlp überspringt den Download, wenn die Datei schon da ist)
    step("1/4  Audio holen")
    t = time.time()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if source.startswith(("http://", "https://")):
        audio_path = download_audio(source)
    else:
        audio_path = import_local(source)
    video_id = audio_path.stem
    timings["Audio holen"] = time.time() - t
    print(f"Audio: {audio_path}")

    # 2) Transkribieren (wird übersprungen, wenn das Transkript schon existiert)
    step("2/4  Transkribieren")
    t = time.time()
    transcript_path = TRANSCRIPT_DIR / f"{video_id}.{model_size}.json"
    if transcript_path.exists():
        print(f"Transkript existiert schon, überspringe: {transcript_path}")
        data = json.loads(transcript_path.read_text(encoding="utf-8"))
    else:
        data = transcribe(audio_path, model_size, language)
        TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
        transcript_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    timings["Transkribieren"] = time.time() - t

    # 3) Abschnitte bilden
    step("3/4  Abschnitte bilden")
    t = time.time()
    meta_path = RAW_DIR / f"{video_id}.meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    chunks = make_chunks(data["segments"], window, overlap)
    for c in chunks:
        c["video_id"] = video_id
        c["title"] = meta.get("title")
        c["url"] = meta.get("url")
    CHUNK_DIR.mkdir(parents=True, exist_ok=True)
    (CHUNK_DIR / f"{video_id}.chunks.json").write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"{len(data['segments'])} Segmente -> {len(chunks)} Abschnitte")
    timings["Abschnitte bilden"] = time.time() - t

    # 4) In die Vektordatenbank schreiben
    step("4/4  In Vektordatenbank schreiben")
    t = time.time()
    total = index_chunks(chunks)
    timings["Indexieren"] = time.time() - t

    # Zusammenfassung
    step("Fertig")
    print(f"Video:      {meta.get('title') or video_id}")
    print(f"Audiolänge: {fmt(data['audio_duration_s'])}\n")
    for name, sec in timings.items():
        print(f"  {name:<20} {sec:8.1f} s")
    print(f"  {'Gesamt':<20} {sum(timings.values()):8.1f} s\n")
    print(f"Abschnitte in der Datenbank (alle Videos): {total}")
    print('Jetzt fragen mit: python src/answer.py "Deine Frage"')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vorlesung komplett verarbeiten")
    parser.add_argument("source", help="Video-URL oder Pfad zu einer lokalen Datei")
    parser.add_argument("--model", default="small", help="Whisper-Modell: tiny | base | small | medium")
    parser.add_argument("--language", default="de")
    args = parser.parse_args()
    run(args.source, args.model, args.language)