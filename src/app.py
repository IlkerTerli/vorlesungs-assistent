"""Schritt 21: Weboberfläche für den Vorlesungs-Assistenten.

Starten mit:
    streamlit run src/app.py
"""
import os

import streamlit as st
from dotenv import load_dotenv

from answer import answer, short_title
from index import get_collection, load_model
from search import fmt, video_link

load_dotenv()

st.set_page_config(page_title="Vorlesungs-Assistent", page_icon="🎓")


@st.cache_resource
def get_model():
    """Embedding-Modell nur einmal laden, nicht bei jeder Frage."""
    return load_model()


def list_lectures() -> list[str]:
    """Alle Vorlesungen, die in der Datenbank stecken."""
    metas = get_collection().get(include=["metadatas"])["metadatas"]
    return sorted({m.get("title") or m.get("video_id") for m in metas})


def show_sources(hits: list[dict]) -> None:
    """Quellen mit Links; das Video der besten Fundstelle wird direkt eingebettet."""
    with st.expander(f"Quellen ({len(hits)})"):
        for i, h in enumerate(hits):
            label = f"{short_title(h)}, {fmt(h['start'])} – {fmt(h['end'])}"
            st.markdown(f"**{label}** · [Im Video öffnen]({video_link(h)})")
            if i == 0 and h.get("url"):
                st.video(h["url"], start_time=int(h["start"]))


# Seitenleiste
with st.sidebar:
    st.header("🎓 Vorlesungs-Assistent")
    st.caption("Fragen zu Vorlesungsvideos – mit Fundstellen direkt im Video.")
    k = st.slider("Abschnitte als Kontext", 1, 8, 3)
    st.subheader("Vorlesungen in der Datenbank")
    for title in list_lectures():
        st.markdown(f"- {title}")
    if st.button("Verlauf löschen"):
        st.session_state.messages = []

if not os.getenv("ANTHROPIC_API_KEY"):
    st.error("Kein API-Schlüssel gefunden. Prüfe die Datei .env im Projektordner.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Bisheriger Verlauf
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            show_sources(msg["hits"])
            st.caption(msg["stats"])

# Neue Frage
if question := st.chat_input("Stell eine Frage zur Vorlesung ..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Suche in den Vorlesungen ..."):
            result = answer(question, k, model=get_model())
        stats = (f"Antwortzeit {result['seconds']:.1f} s · "
                 f"Tokens: {result['input_tokens']} rein, {result['output_tokens']} raus")
        st.markdown(result["answer"])
        show_sources(result["hits"])
        st.caption(stats)

    st.session_state.messages.append(
        {"role": "assistant", "content": result["answer"], "hits": result["hits"], "stats": stats}
    )