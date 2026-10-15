"""Schritt 1b: Audio transkribieren und Segmente mit Zeitstempeln speichern.

Beispiel:
    python src/transcribe.py data/raw/abc123.m4a --model small
"""
import argparse
import json
import time
from pathlib import Path

from faster_whisper import WhisperModel

OUT_DIR = Path("data/transcripts")


def pick_device() -> tuple[str, str]:
    """Nutzt die Grafikkarte, falls vorhanden, sonst die CPU."""
    try:
        import ctranslate2

        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda", "float16"
    except Exception:
        pass
    return "cpu", "int8"


def fmt(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def transcribe(audio_path: Path, model_size: str, language: str) -> dict:
    device, compute_type = pick_device()
    print(f"Modell: {model_size} | Gerät: {device} ({compute_type})")
    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    start = time.time()
    segments, info = model.transcribe(
        str(audio_path), language=language, vad_filter=True  # VAD überspringt Stille
    )

    result = []
    for seg in segments:  # Transkription läuft während dieser Schleife
        text = seg.text.strip()
        result.append({"start": round(seg.start, 2), "end": round(seg.end, 2), "text": text})
        print(f"[{fmt(seg.start)}] {text}")

    processing_s = time.time() - start
    return {
        "source": str(audio_path),
        "model": model_size,
        "device": device,
        "language": info.language,
        "audio_duration_s": round(info.duration, 1),
        "processing_s": round(processing_s, 1),
        "segments": result,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vorlesung transkribieren")
    parser.add_argument("audio", help="Pfad zur Audiodatei in data/raw")
    parser.add_argument("--model", default="small", help="tiny | base | small | medium | large-v3")
    parser.add_argument("--language", default="de")
    args = parser.parse_args()

    audio = Path(args.audio)
    data = transcribe(audio, args.model, args.language)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_json = OUT_DIR / f"{audio.stem}.{args.model}.json"
    out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    out_txt = out_json.with_suffix(".txt")
    out_txt.write_text(
        "\n".join(f"[{fmt(s['start'])}] {s['text']}" for s in data["segments"]),
        encoding="utf-8",
    )

    ratio = data["processing_s"] / max(data["audio_duration_s"], 1)
    print(f"\nFertig: {out_json}")
    print(f"Audio: {fmt(data['audio_duration_s'])} | Rechenzeit: {fmt(data['processing_s'])} "
          f"| Faktor: {ratio:.2f}x Echtzeit")
