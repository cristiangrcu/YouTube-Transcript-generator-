from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from dotenv import load_dotenv

from transcript import fetch_transcript, TranscriptError
from formats import to_txt, to_srt, to_vtt
from summary import summarize, SummaryError

load_dotenv()

app = FastAPI(title="YouTube Transcript Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class UrlIn(BaseModel):
    url: str
    languages: list[str] | None = None


class SummaryIn(BaseModel):
    transcript: str
    language: str | None = None


class DownloadIn(BaseModel):
    entries: list[dict]
    format: str


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/transcript")
def get_transcript(payload: UrlIn):
    try:
        return fetch_transcript(payload.url, payload.languages)
    except TranscriptError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/summary")
def get_summary(payload: SummaryIn):
    try:
        text = summarize(payload.transcript, payload.language)
        return {"summary": text}
    except SummaryError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/download")
def download(payload: DownloadIn):
    fmt = payload.format.lower()
    if fmt == "txt":
        body = to_txt(payload.entries)
        media = "text/plain"
    elif fmt == "srt":
        body = to_srt(payload.entries)
        media = "application/x-subrip"
    elif fmt == "vtt":
        body = to_vtt(payload.entries)
        media = "text/vtt"
    else:
        raise HTTPException(status_code=400, detail="Unbekanntes Format.")

    return Response(
        content=body,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="transcript.{fmt}"'},
    )
