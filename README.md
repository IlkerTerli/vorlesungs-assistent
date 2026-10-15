# Vorlesungs-Assistent

Transkribiert Vorlesungen, beantwortet Fragen zum Stoff mit Fundstelle im Video
und erstellt Zusammenfassungen und Karteikarten.

## Setup

```bash
python -m venv .venv
# Windows:      .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
```

## Schritt 1: Transkription

```bash
python src/ingest.py "<Video-URL oder lokale Datei>"
python src/transcribe.py data/raw/<datei> --model small
```

Ergebnis: `data/transcripts/<datei>.<modell>.json` (Segmente mit Zeitstempeln)
und eine lesbare `.txt`-Version.

## Struktur

```
src/
  ingest.py       Audio holen (URL oder lokale Datei) + Metadaten
  transcribe.py   Whisper-Transkription mit Zeitstempeln
data/             (nicht im Repo) Rohdaten und Ergebnisse
```
