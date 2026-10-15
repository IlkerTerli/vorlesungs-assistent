"""Schritt 1a: Audio aus einem Video-Link holen oder eine lokale Datei übernehmen.

Beispiele:
    python src/ingest.py "https://www.youtube.com/watch?v=..."
    python src/ingest.py "C:/Downloads/vorlesung.mp4"
"""
import argparse
import json
import shutil
from pathlib import Path

import yt_dlp

RAW_DIR = Path("data/raw")


def download_audio(url: str) -> Path:
    """Lädt nur die Tonspur herunter (kein ffmpeg nötig) und speichert Metadaten."""
    opts = {
        "format": "bestaudio[ext=m4a]/bestaudio",
        "outtmpl": str(RAW_DIR / "%(id)s.%(ext)s"),
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        audio_path = Path(ydl.prepare_filename(info))

    # Metadaten brauchen wir später für die Fundstellen-Links ("Minute 32:15")
    meta = {
        "id": info.get("id"),
        "title": info.get("title"),
        "url": url,
        "duration_s": info.get("duration"),
        "license": info.get("license"),
    }
    audio_path.with_suffix(".meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return audio_path


def import_local(path: str) -> Path:
    """Kopiert eine lokale Audio- oder Videodatei nach data/raw."""
    src = Path(path)
    dst = RAW_DIR / src.name
    shutil.copy(src, dst)
    meta = {"id": src.stem, "title": src.stem, "url": None, "source_file": str(src)}
    dst.with_suffix(".meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return dst


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vorlesung (Audio) einlesen")
    parser.add_argument("source", help="Video-URL oder Pfad zu einer lokalen Datei")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if args.source.startswith(("http://", "https://")):
        path = download_audio(args.source)
    else:
        path = import_local(args.source)
    print(f"Gespeichert: {path}")
