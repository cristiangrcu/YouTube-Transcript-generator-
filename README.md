# YouTube Transcript Generator

Ein Tool, mit dem man einen YouTube-Link einfügt und **das Original-Transkript
von YouTube 1:1 zurückbekommt** — kein Umformulieren, kein Ersetzen von Wörtern.
Zusätzlich gibt es Downloads als `.txt`, `.srt` und `.vtt` und eine optionale
KI-Zusammenfassung.

## Projektstruktur

```
backend/    Python FastAPI — holt Transkript & baut Downloads
frontend/   Next.js UI — Link-Input, Anzeige, Buttons
```

## Was macht was

- **`backend/transcript.py`** — extrahiert die Video-ID aus jedem gängigen
  YouTube-Link-Format und holt das Transkript über `youtube-transcript-api`.
  Wenn kein Transkript existiert, kommt eine klare Fehlermeldung zurück.
- **`backend/formats.py`** — konvertiert die Segmente in `.txt`, `.srt` oder `.vtt`.
- **`backend/summary.py`** — optionale KI-Zusammenfassung über Claude (Anthropic).
  Läuft nur wenn der Nutzer auf den Button drückt und ein API-Key gesetzt ist.
- **`frontend/app/page.tsx`** — Eingabefeld, Segment-Liste mit Zeitstempeln,
  Download-Buttons und Zusammenfassungs-Button.

## Setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# ANTHROPIC_API_KEY eintragen (nur nötig für die KI-Zusammenfassung)

uvicorn main:app --reload --port 8000
```

Läuft dann auf `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local

npm run dev
```

Läuft dann auf `http://localhost:3000`.

## Bedienung

1. YouTube-Link ins Eingabefeld pasten (jedes Format geht — `youtu.be/…`,
   `youtube.com/watch?v=…`, `youtube.com/shorts/…`, `youtube.com/embed/…`).
2. **Transkript holen** klicken → Original-Transkript erscheint mit Zeitstempeln.
3. Über die Buttons als `.txt`, `.srt` oder `.vtt` herunterladen.
4. Optional: **KI-Zusammenfassung** — separates Feature, das Transkript selbst
   bleibt davon unangetastet.

## API (Backend)

- `POST /api/transcript` — `{ "url": "..." }` → Transkript-Segmente
- `POST /api/download` — `{ "entries": [...], "format": "txt|srt|vtt" }` → Datei
- `POST /api/summary` — `{ "transcript": "...", "language": "de" }` → KI-Text
- `GET /api/health` — Health-Check
