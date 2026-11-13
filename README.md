# Vorlesungs-Assistent

Fragen an Vorlesungsvideos – mit Antwort und Fundstelle direkt im Video.

Projekt im Modul „KI in der Anwendung“, M.Sc. Wirtschaftsinformatik, Hochschule Worms.
Projektteam: Akif, Burak, Ilker Terli

## Funktionsweise

Das System hat zwei Phasen:

**1. Vorlesung einlesen** (einmal pro Video, `pipeline.py`)
YouTube-Link → Audio (yt-dlp) → Transkript mit Zeitstempeln (Whisper small) → Abschnitte (60 s, 10 s Überlappung) → Embeddings (multilingual-e5-small) → Vektordatenbank (ChromaDB)

**2. Frage beantworten** (bei jeder Frage, `app.py` bzw. `answer.py`)
Frage → semantische Suche (Top-3-Abschnitte über alle Vorlesungen) → Antwort mit Claude Haiku 5.5 (RAG) → Antwort mit Fundstellen und eingebettetem Video, das an der passenden Stelle startet

Transkription, Embeddings und Datenbank laufen lokal. Nur die Antwortformulierung nutzt die Claude-API; dabei werden ausschließlich die Frage und die drei gefundenen Abschnitte übertragen.

## Modelle

| Modell | Aufgabe | Modellart | Läuft |
|---|---|---|---|
| Whisper small (via faster-whisper) | Sprache → Text mit Zeitstempeln | Speech-to-Text | lokal |
| intfloat/multilingual-e5-small | Text → Vektor für die Suche | Feature Extraction | lokal |
| Claude Haiku 5.5 (Anthropic) | Antwort aus den Fundstellen formulieren | Text Generation | API |

Alle Modelle sind vortrainiert, es findet kein eigenes Training statt.

## Setup

```bash
python -m venv .venv
# Windows:      .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
```

Für die Antworten wird ein API-Schlüssel von Anthropic benötigt. Dazu im Projektordner eine Datei `.env` anlegen:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Die `.env` ist in der `.gitignore` eingetragen und wird nie committet.

## Nutzung

**Vorlesung einlesen** (Link oder lokale Video-/Audiodatei):

```bash
python src/pipeline.py "https://www.youtube.com/watch?v=..."
```

Bereits erledigte Schritte (Download, Transkript) werden bei einem erneuten Lauf übersprungen.

**Fragen im Terminal:**

```bash
python src/answer.py "Was ist eine Teilmenge?"
```

**Weboberfläche:**

```bash
streamlit run src/app.py
```

Danach im Browser `http://localhost:8501` öffnen.

## Projektstruktur

```
src/
  ingest.py       Audio holen (URL oder lokale Datei) + Metadaten
  transcribe.py   Whisper-Transkription mit Zeitstempeln
  chunk.py        Transkript in Abschnitte zerlegen
  index.py        Embeddings berechnen und in ChromaDB speichern
  search.py       Semantische Suche mit Fundstellen-Links
  answer.py       Antwort mit Claude (RAG)
  pipeline.py     Alle Schritte vom Link bis zur Datenbank in einem Befehl
  app.py          Weboberfläche mit Streamlit
.streamlit/
  config.toml     Streamlit-Konfiguration
data/             (nicht im Repo) Audio, Transkripte, Abschnitte, Datenbank
```

## Erste Messwerte (Mid-Term)

Testdaten: zwei öffentliche Vorlesungen (LinADI 1a und 1b, zusammen 69 Minuten), Laptop ohne GPU.

| Messgröße | Wert |
|---|---|
| Transkriptionszeit relativ zur Videolänge | 0,84 (1a) bzw. 0,63 (1b) |
| Pipeline gesamt für 43 min Video | ca. 28 min, erneuter Lauf ca. 13 s |
| Antwortzeit pro Frage | 3–7 s |
| Tokens pro Frage (Eingabe) | ca. 1.700–2.000 |

## Ausblick

- Folienerkennung im Video (OpenCV) und Folientext per OCR
- Fachbegriffe aus den Folien (spaCy) als Hinweis für Whisper
- Evaluation: Word Error Rate gegen Referenztranskript, Testfragen mit erwarteten Antworten
- Mindest-Ähnlichkeit, damit Fragen außerhalb des Stoffs ohne API-Aufruf beantwortet werden

## Hinweise

Die verwendeten Vorlesungsvideos sind öffentlich zugänglich und dienen nur als Testdaten für dieses Studienprojekt. Videos, Audio, Transkripte und Datenbank liegen ausschließlich lokal im Ordner `data/` und sind nicht Teil des Repositorys.