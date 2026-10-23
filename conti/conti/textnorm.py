"""Text clean-up shared by the extractors. Nothing here changes a transcription: it makes working copies.

clean(s)  the text as transcribed, minus editorial markup: [del: …] dropped, [ins: …] kept, [?] dropped, ___ → space.
plain(s)  clean(s) folded for pattern matching: macrons/tildes dropped (an̄o → ano), ƀ → b, ꝑ → per, ꝓ → pro,
          ꝙ → qu, ⁊ → e, ꝯ → con, 𝒹 → d, ſ → s, superscripts → letters, lower case.
"""
from __future__ import annotations

import re
import unicodedata

_DEL = re.compile(r"\[del:[^\]]*\]")
_INS = re.compile(r"\[ins:\s*([^\]]*)\]")
_Q = re.compile(r"\[\?\]")
_DASH = re.compile(r"_{2,}")

_MAP = {"ƀ": "b", "ꝑ": "per", "ꝓ": "pro", "ꝙ": "qu", "⁊": "e", "ꝯ": "con", "𝒹": "d", "ſ": "s", "ł": "l",
        "ª": "a", "ᵃ": "a", "ᵒ": "", "º": "", "°": "", "ͣ": "a", "ͥ": "i", "ꝫ": "et", "ꝰ": "us", "ħ": "h",
        "ß": "ß", "ƒ": "ƒ"}


def clean(s: str) -> str:
    s = unicodedata.normalize("NFC", s or "")
    s = _DEL.sub(" ", s)
    s = _INS.sub(lambda m: m.group(1), s)
    s = _Q.sub(" ", s)
    s = _DASH.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


def uncertain(s: str) -> bool:
    return "[?]" in (s or "")


def plain(s: str) -> str:
    s = clean(s)
    s = "".join(_MAP.get(ch, ch) for ch in s)
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return unicodedata.normalize("NFC", s).lower()
