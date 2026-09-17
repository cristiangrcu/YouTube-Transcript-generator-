import re
from urllib.parse import urlparse, parse_qs

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)


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
