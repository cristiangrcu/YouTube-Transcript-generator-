import os

import anthropic


class SummaryError(Exception):
    pass


SYSTEM_PROMPT = (
    "Du bekommst das Transkript eines YouTube-Videos. Fasse den Inhalt klar, "
    "sachlich und in derselben Sprache wie das Transkript zusammen. Struktur:\n"
    "1) Ein Satz Kern-Aussage\n"
    "2) 3–6 stichpunktartige Kernpunkte\n"
    "3) (optional) 1–2 Sätze Kontext oder Fazit\n"
    "Erfinde nichts, was nicht im Transkript steht."
)


def summarize(transcript_text: str, language_hint: str | None = None) -> str:
    if not transcript_text.strip():
        raise SummaryError("Transkript ist leer.")

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise SummaryError(
            "ANTHROPIC_API_KEY ist nicht gesetzt. Trag ihn in backend/.env ein."
        )

    client = anthropic.Anthropic()

    user_prefix = ""
    if language_hint:
        user_prefix = f"Sprache des Transkripts: {language_hint}\n\n"

    try:
        with client.messages.stream(
            model="claude-opus-5",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            thinking={"type": "adaptive"},
            messages=[
                {
                    "role": "user",
                    "content": user_prefix + "Transkript:\n\n" + transcript_text,
                }
            ],
        ) as stream:
            final = stream.get_final_message()
    except anthropic.APIError as e:
        raise SummaryError(f"Claude-API Fehler: {e}")

    parts = [block.text for block in final.content if block.type == "text"]
    return "\n".join(parts).strip()
