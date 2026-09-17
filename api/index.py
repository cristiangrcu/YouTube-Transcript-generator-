import re
from urllib.parse import urlparse, parse_qs

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)


app = FastAPI(title="YouTube Transcript Generator")


class TranscriptError(Exception):
    pass


def extract_video_id(url: str) -> str:
    url = url.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url):
        return url

    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()

    if host in ("youtu.be", "www.youtu.be"):
        vid = parsed.path.lstrip("/").split("/")[0]
        if vid:
            return vid

    if host.endswith("youtube.com") or host.endswith("youtube-nocookie.com"):
        qs = parse_qs(parsed.query)
        if "v" in qs and qs["v"]:
            return qs["v"][0]
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) >= 2 and parts[0] in ("embed", "shorts", "live", "v"):
            return parts[1]

    raise TranscriptError("Konnte keine gültige YouTube-Video-ID aus dem Link lesen.")


def fetch_transcript(url: str, preferred_languages: list[str] | None = None) -> dict:
    video_id = extract_video_id(url)
    languages = preferred_languages or ["de", "en"]

    try:
        transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
    except TranscriptsDisabled:
        raise TranscriptError("Für dieses Video sind Untertitel deaktiviert.")
    except VideoUnavailable:
        raise TranscriptError("Das Video ist nicht verfügbar.")
    except Exception as e:
        raise TranscriptError(f"YouTube konnte nicht abgefragt werden: {e}")

    transcript = None
    try:
        transcript = transcripts.find_manually_created_transcript(languages)
    except NoTranscriptFound:
        try:
            transcript = transcripts.find_generated_transcript(languages)
        except NoTranscriptFound:
            for t in transcripts:
                transcript = t
                break

    if transcript is None:
        raise TranscriptError("Für dieses Video wurde kein Transkript auf YouTube gefunden.")

    entries = transcript.fetch()

    return {
        "video_id": video_id,
        "language": transcript.language_code,
        "language_name": transcript.language,
        "is_generated": transcript.is_generated,
        "entries": [
            {
                "text": entry["text"],
                "start": float(entry["start"]),
                "duration": float(entry["duration"]),
            }
            for entry in entries
        ],
    }


def _timestamp(seconds: float, sep: str) -> str:
    if seconds < 0:
        seconds = 0
    ms = int(round((seconds - int(seconds)) * 1000))
    total = int(seconds)
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def to_txt(entries: list[dict]) -> str:
    return "\n".join(entry["text"] for entry in entries)


def to_srt(entries: list[dict]) -> str:
    lines = []
    for i, entry in enumerate(entries, start=1):
        start = entry["start"]
        end = start + entry["duration"]
        lines.append(str(i))
        lines.append(f"{_timestamp(start, ',')} --> {_timestamp(end, ',')}")
        lines.append(entry["text"])
        lines.append("")
    return "\n".join(lines)


def to_vtt(entries: list[dict]) -> str:
    lines = ["WEBVTT", ""]
    for entry in entries:
        start = entry["start"]
        end = start + entry["duration"]
        lines.append(f"{_timestamp(start, '.')} --> {_timestamp(end, '.')}")
        lines.append(entry["text"])
        lines.append("")
    return "\n".join(lines)


class UrlIn(BaseModel):
    url: str
    languages: list[str] | None = None


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
