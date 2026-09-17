# YouTube Transcript Generator

Link einfügen → Original-Transkript von YouTube 1:1 zurückbekommen (kein
Umformulieren, keine Wortänderungen). Downloads als `.txt`, `.srt` und `.vtt`.

Läuft als Next.js-Frontend + Python-Serverless-Function auf Vercel.

## Projektstruktur

```
api/index.py          FastAPI-App (Serverless Function auf Vercel)
app/                  Next.js-Frontend
requirements.txt      Python-Deps für die Serverless Function
vercel.json           Routing /api/* → api/index.py
package.json          Next.js-Deps
```

## Deployment auf Vercel

Repo mit Vercel verknüpfen — Vercel erkennt automatisch:

- Next.js im Root → wird gebaut & gehostet
- `api/index.py` + `requirements.txt` → Python-Serverless-Function
- `vercel.json` sorgt dafür, dass `/api/*` alle an die FastAPI-App gehen

Keine Env-Variablen nötig.

## Lokale Entwicklung

Am einfachsten mit der Vercel CLI (alles auf `localhost:3000`):

```bash
npm install
npm install -g vercel
vercel dev
```

Alternativ getrennt (Python-Backend separat auf `:8000`):

```bash
# Terminal 1 - Python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt uvicorn
uvicorn api.index:app --reload --port 8000

# Terminal 2 - Next.js
npm install
cp .env.local.example .env.local
# in .env.local NEXT_PUBLIC_API_URL=http://localhost:8000 eintragen
npm run dev
```

## API

- `POST /api/transcript` — `{ "url": "..." }` → Transkript-Segmente
- `POST /api/download` — `{ "entries": [...], "format": "txt|srt|vtt" }` → Datei
- `GET /api/health` — Health-Check

## Bekanntes Risiko

`youtube-transcript-api` nutzt inoffizielle YouTube-Endpoints. YouTube blockiert
manchmal Cloud-IPs (Vercel, AWS, …). Wenn's auf Vercel nicht sauber läuft, ist
der übliche Fix ein Umzug des Python-Teils auf Railway / Fly.io.
