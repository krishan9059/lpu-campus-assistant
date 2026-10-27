"""Language handling for English, Hindi and Punjabi."""

from __future__ import annotations

from typing import Literal

Language = Literal["en", "hi", "pa"]

_DEVANAGARI = (0x0900, 0x097F)
_GURMUKHI = (0x0A00, 0x0A7F)
_INDIC_SHARE_THRESHOLD = 0.3

LANGUAGE_INSTRUCTIONS: dict[str, str] = {
    "en": "Reply in English.",
    "hi": (
        "Reply in Hindi, written in Devanagari script. Keep names, numbers, codes, URLs and "
        "e-mail addresses exactly as they appear in the passages."
    ),
    "pa": (
        "Reply in Punjabi, written in Gurmukhi script. Keep names, numbers, codes, URLs and "
        "e-mail addresses exactly as they appear in the passages."
    ),
    "auto": (
        "Reply in the same language and script as the user's latest message (English, Hindi in "
        "Devanagari, or Punjabi in Gurmukhi). If unsure, reply in English."
    ),
}


def detect_language(text: str) -> Language:
    """Detect by script. Romanised Hindi is indistinguishable from English here and is
    treated as English; the model still answers in the user's own register."""
    devanagari = gurmukhi = latin = 0
    for char in text:
        code = ord(char)
        if _DEVANAGARI[0] <= code <= _DEVANAGARI[1]:
            devanagari += 1
        elif _GURMUKHI[0] <= code <= _GURMUKHI[1]:
            gurmukhi += 1
        elif char.isascii() and char.isalpha():
            latin += 1
    indic = devanagari + gurmukhi
    if indic == 0 or indic / (indic + latin) < _INDIC_SHARE_THRESHOLD:
        return "en"
    return "pa" if gurmukhi > devanagari else "hi"


def resolve_language(requested: str, message: str) -> Language:
    if requested in ("en", "hi", "pa"):
        return requested  # type: ignore[return-value]
    return detect_language(message)


def instruction_for(requested: str) -> str:
    return LANGUAGE_INSTRUCTIONS.get(requested, LANGUAGE_INSTRUCTIONS["auto"])
