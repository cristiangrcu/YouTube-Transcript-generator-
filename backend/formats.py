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
