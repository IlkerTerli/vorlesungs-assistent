"""Schritt 15: Fragen zur Vorlesung beantworten (RAG mit Claude).

Beispiel:
    python src/answer.py "Was ist eine Menge?"
"""
import argparse
import os
import sys
import time

import anthropic
from dotenv import load_dotenv

from search import fmt, search, video_link

load_dotenv()  # liest ANTHROPIC_API_KEY aus der .env

MODEL = "claude-haiku-5-5"

SYSTEM_PROMPT = """Du bist ein Lernassistent für Studierende und beantwortest Fragen zu einer Vorlesung.
Regeln:
- Antworte ausschließlich auf Basis der bereitgestellten Ausschnitte aus dem Vorlesungstranskript.
- Wenn die Ausschnitte die Frage nicht beantworten, sag das ehrlich, statt etwas zu erfinden.
- Gib bei jeder Aussage die Fundstelle als Zeitstempel in eckigen Klammern an, z. B. [00:08:09].
- Das Transkript wurde automatisch erstellt und kann Erkennungsfehler enthalten.
  Korrigiere offensichtliche Fehler in deiner Antwort stillschweigend.
- Antworte auf Deutsch, klar verständlich und kurz (höchstens etwa 200 Wörter)."""


def build_context(hits: list[dict]) -> str:
    """Formatiert die gefundenen Abschnitte mit Zeitstempeln für das Sprachmodell."""
    parts = [f"[{fmt(h['start'])} - {fmt(h['end'])}]\n{h['text']}" for h in hits]
    return "\n\n---\n\n".join(parts)


def answer(question: str, k: int = 3) -> dict:
    hits = search(question, k)
    prompt = f"Ausschnitte aus der Vorlesung:\n\n{build_context(hits)}\n\nFrage: {question}"

    client = anthropic.Anthropic()  # nutzt automatisch ANTHROPIC_API_KEY
    start = time.time()
    response = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")

    return {
        "answer": text,
        "hits": hits,
        "seconds": time.time() - start,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "stop_reason": response.stop_reason,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fragen zur Vorlesung beantworten")
    parser.add_argument("question", help="Deine Frage in Anführungszeichen")
    parser.add_argument("-k", type=int, default=3, help="Anzahl der Abschnitte als Kontext")
    args = parser.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit("Kein API-Schlüssel gefunden. Prüfe die Datei .env im Projektordner.")

    result = answer(args.question, args.k)

    print("\n=== Antwort ===\n")
    print(result["answer"])
    print("\n=== Quellen ===")
    for h in result["hits"]:
        print(f"[{fmt(h['start'])} - {fmt(h['end'])}]  {video_link(h)}")
    print(f"\nAntwortzeit: {result['seconds']:.1f} s | "
          f"Tokens: {result['input_tokens']} rein, {result['output_tokens']} raus")

    if result["stop_reason"] == "max_tokens":
        print("Hinweis: Die Antwort wurde wegen des Token-Limits abgeschnitten.")