"""
Emoji enrichment: annotates transcribed text with contextually fitting emojis.

Strategy: rule-based keyword→emoji dictionary.
- One compiled regex pass over the text (efficient, no repeated scans)
- Keywords sorted by length descending so longer matches (e.g. "krankenhaus")
  take priority over shorter sub-words (e.g. "haus")
- Word boundaries (\b) prevent partial-word matches inside compound words
- Case-insensitive, Unicode-aware
"""

from __future__ import annotations

import re
from typing import Iterable

# ---------------------------------------------------------------------------
# Declarative source: language → emoji → keywords
# ---------------------------------------------------------------------------

EMOJI_KEYWORDS_BY_LANGUAGE: dict[str, dict[str, tuple[str, ...]]] = {
    "de": {
        "☕": ("kaffee",),
        "🍵": ("tee",),
        "🍺": ("bier",),
        "🍷": ("wein",),
        "🍕": ("pizza",),
        "🍔": ("burger",),
        "🍣": ("sushi",),
        "🎂": ("kuchen", "torte", "geburtstag"),
        "🍞": ("brot",),
        "💧": ("wasser",),
        "🍎": ("apfel",),
        "🍌": ("banane",),
        "🍓": ("erdbeere",),
        "🥗": ("salat",),
        "🍫": ("schokolade",),
        "🍦": ("eis",),
        "🍲": ("suppe",),
        "🧀": ("käse",),
        "☀️": ("sonne", "sonnig"),
        "🌧️": ("regen", "regnerisch"),
        "❄️": ("schnee",),
        "☁️": ("wolke", "wolken"),
        "⛈️": ("gewitter",),
        "💨": ("wind",),
        "🌫️": ("nebel",),
        "🌈": ("regenbogen",),
        "⚡": ("blitz",),
        "😊": ("freude", "glück"),
        "😢": ("trauer", "traurig"),
        "❤️": ("liebe", "herz"),
        "😂": ("lachen",),
        "😭": ("weinen",),
        "😡": ("wut",),
        "😨": ("angst",),
        "😲": ("überraschung",),
        "🏥": ("krankenhaus",),
        "🛒": ("supermarkt",),
        "🍽️": ("restaurant",),
        "🏖️": ("strand", "ferien"),
        "⛰️": ("berg",),
        "🏫": ("schule",),
        "💼": ("büro", "arbeit"),
        "⛪": ("kirche",),
        "🏠": ("haus",),
        "🌳": ("park", "baum"),
        "🏙️": ("stadt",),
        "✈️": ("flugzeug", "urlaub", "reisen"),
        "🏍️": ("motorrad",),
        "🚲": ("fahrrad",),
        "🚀": ("rakete",),
        "🚢": ("schiff",),
        "🚂": ("zug",),
        "🚗": ("auto",),
        "🚕": ("taxi",),
        "🚌": ("bus",),
        "⚽": ("fußball",),
        "🎾": ("tennis",),
        "🏊": ("schwimmen",),
        "🏃": ("laufen",),
        "🥊": ("boxen",),
        "🧘": ("yoga",),
        "⛳": ("golf",),
        "🏋️": ("sport",),
        "🦋": ("schmetterling",),
        "🐘": ("elefant",),
        "🦁": ("löwe",),
        "🐴": ("pferd",),
        "🌸": ("blume",),
        "🐶": ("hund",),
        "🐱": ("katze",),
        "🐦": ("vogel",),
        "🐟": ("fisch",),
        "🐻": ("bär",),
        "💻": ("computer", "laptop"),
        "📱": ("handy", "telefon"),
        "📷": ("kamera",),
        "🎵": ("musik",),
        "📚": ("buch",),
        "📺": ("fernsehen",),
        "🔥": ("feuer",),
        "⭐": ("stern",),
        "💰": ("geld",),
        "😴": ("schlafen",),
        "🌙": ("nacht",),
        "🌅": ("morgen",),
        "🎉": ("party",),
        "🙏": ("danke",),
        "👋": ("hallo", "tschüss"),
    },
    "en": {
        "☕": ("coffee",),
        "🍵": ("tea",),
        "🍺": ("beer",),
        "🍷": ("wine",),
        "🍕": ("pizza",),
        "🍔": ("burger",),
        "🍣": ("sushi",),
        "🍞": ("bread",),
        "💧": ("water",),
        "🍎": ("apple",),
        "🍌": ("banana",),
        "🍓": ("strawberry",),
        "🥗": ("salad",),
        "🍫": ("chocolate",),
        "🍲": ("soup",),
        "🧀": ("cheese",),
        "☀️": ("sun",),
        "🌧️": ("rain",),
        "❄️": ("snow",),
        "☁️": ("cloud",),
        "⛈️": ("thunderstorm",),
        "🌫️": ("fog",),
        "🌈": ("rainbow",),
        "⚡": ("lightning",),
        "😊": ("happy",),
        "😢": ("sad",),
        "❤️": ("love", "heart"),
        "😂": ("laugh",),
        "😭": ("cry",),
        "😡": ("angry",),
        "😨": ("fear",),
        "😲": ("surprise",),
        "🏥": ("hospital",),
        "🛒": ("supermarket",),
        "🍽️": ("restaurant",),
        "🏖️": ("beach", "vacation"),
        "⛰️": ("mountain",),
        "🏫": ("school",),
        "💼": ("office", "work"),
        "⛪": ("church",),
        "🏠": ("house",),
        "🌳": ("park", "tree"),
        "🏙️": ("city",),
        "✈️": ("plane", "travel"),
        "🏍️": ("motorcycle",),
        "🚲": ("bicycle", "bike"),
        "🚀": ("rocket",),
        "🚢": ("ship",),
        "🚂": ("train",),
        "🚗": ("car",),
        "🚕": ("taxi",),
        "🚌": ("bus",),
        "🏀": ("basketball",),
        "⚽": ("soccer", "football"),
        "🎾": ("tennis",),
        "🏊": ("swimming",),
        "🏃": ("running",),
        "🥊": ("boxing",),
        "🧘": ("yoga",),
        "⛳": ("golf",),
        "🦋": ("butterfly",),
        "🐘": ("elephant",),
        "🦁": ("lion",),
        "🐴": ("horse",),
        "🌸": ("flower",),
        "🐶": ("dog",),
        "🐱": ("cat",),
        "🐦": ("bird",),
        "🐟": ("fish",),
        "🐻": ("bear",),
        "💻": ("computer", "laptop"),
        "📱": ("phone",),
        "📷": ("camera",),
        "🎵": ("music",),
        "📚": ("book",),
        "📺": ("television",),
        "🎂": ("birthday",),
        "🔥": ("fire",),
        "⭐": ("star",),
        "💰": ("money",),
        "😴": ("sleep",),
        "🌙": ("night",),
        "🌅": ("morning",),
        "🎉": ("party",),
        "🙏": ("thanks",),
        "👋": ("hello", "bye"),
    },
    "pl": {
        "☕": ("kawa",),
        "🍺": ("piwo",),
        "🍷": ("wino",),
        "🍕": ("pizza",),
        "🍔": ("burger",),
        "🍣": ("sushi",),
        "🍞": ("chleb",),
        "💧": ("woda",),
        "🍎": ("jabłko", "jablko"),
        "🍌": ("banan",),
        "🥗": ("sałatka", "salatka"),
        "🍲": ("zupa",),
        "🧀": ("ser",),
        "☀️": ("słońce", "slonce"),
        "🌧️": ("deszcz",),
        "❄️": ("śnieg", "snieg"),
        "☁️": ("chmura",),
        "⛈️": ("burza",),
        "💨": ("wiatr",),
        "🌫️": ("mgła", "mgla"),
        "🌈": ("tęcza", "tecza"),
        "⚡": ("błyskawica", "blyskawica"),
        "😊": ("radość", "radosc"),
        "😢": ("smutek",),
        "❤️": ("miłość", "milosc"),
        "😡": ("złość", "zlosc"),
        "😨": ("strach",),
        "🏥": ("szpital",),
        "🛒": ("sklep",),
        "🍽️": ("restaurant",),
        "🏖️": ("plaża", "plaza"),
        "⛰️": ("góra", "gora"),
        "🏫": ("szkoła", "szkola"),
        "💼": ("biuro", "praca"),
        "🏠": ("dom",),
        "🌳": ("park", "drzewo"),
        "🏙️": ("miasto",),
        "✈️": ("samolot", "podróż", "podroz"),
        "🚲": ("rower",),
        "🚢": ("statek",),
        "🚂": ("pociąg", "pociag"),
        "🚗": ("samochód", "samochod"),
        "🚕": ("taxi",),
        "🚌": ("bus",),
        "⚽": ("piłka", "pilka"),
        "🎾": ("tennis",),
        "🏊": ("pływanie", "plywanie"),
        "🏃": ("bieganie",),
        "🧘": ("yoga",),
        "⛳": ("golf",),
        "🌸": ("kwiat",),
        "🐶": ("pies",),
        "🐱": ("kot",),
        "🐦": ("ptak",),
        "🐟": ("ryba",),
        "💻": ("computer", "laptop"),
        "📱": ("telefon", "telefon komórkowy", "telefon komorkowy"),
        "📷": ("kamera",),
        "🎵": ("muzyka",),
        "📚": ("książka", "ksiazka"),
        "🔥": ("fire",),
        "⭐": ("star",),
        "💰": ("money",),
        "😴": ("sleep",),
        "🌙": ("night",),
        "🌅": ("morning",),
        "🎉": ("party",),
        "🙏": ("dziękuję", "dziekuje"),
        "👋": ("dzień dobry", "dzien dobry", "cześć", "czesc"),
    },
}


def _build_language_emoji_maps() -> dict[str, dict[str, str]]:
    language_maps: dict[str, dict[str, str]] = {}
    for language, emoji_keywords in EMOJI_KEYWORDS_BY_LANGUAGE.items():
        scoped_map: dict[str, str] = {}
        for emoji, keywords in emoji_keywords.items():
            for keyword in keywords:
                existing = scoped_map.get(keyword)
                if existing is not None and existing != emoji:
                    raise ValueError(
                        f"Duplicate keyword '{keyword}' in language '{language}' maps to both '{existing}' and '{emoji}'."
                    )
                scoped_map[keyword] = emoji
        language_maps[language] = scoped_map
    return language_maps


def _merge_language_maps(language_maps: dict[str, dict[str, str]]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for language, scoped_map in language_maps.items():
        for keyword, emoji in scoped_map.items():
            existing = merged.get(keyword)
            if existing is not None and existing != emoji:
                raise ValueError(
                    f"Keyword '{keyword}' conflicts across languages: '{existing}' vs '{emoji}' (latest from '{language}')."
                )
            merged[keyword] = emoji
    return merged


LANGUAGE_EMOJI_MAPS: dict[str, dict[str, str]] = _build_language_emoji_maps()
LANGUAGE_KEYWORDS: dict[str, set[str]] = {
    language: set(scoped_map.keys()) for language, scoped_map in LANGUAGE_EMOJI_MAPS.items()
}
EMOJI_MAP: dict[str, str] = _merge_language_maps(LANGUAGE_EMOJI_MAPS)

# ---------------------------------------------------------------------------
# Regex cache by language scope
# ---------------------------------------------------------------------------

def _build_pattern(keywords: Iterable[str]) -> re.Pattern | None:
    # Longer keywords first → prevents "haus" matching before "krankenhaus"
    sorted_keywords = sorted(set(keywords), key=len, reverse=True)
    if not sorted_keywords:
        return None
    escaped = [re.escape(k) for k in sorted_keywords]
    pattern = r"\b(" + "|".join(escaped) + r")\b"
    return re.compile(pattern, re.IGNORECASE | re.UNICODE)


_PATTERN_CACHE: dict[str, re.Pattern] = {}


def _normalize_language(language: str | None) -> str:
    if not language:
        return "all"
    lang = language.strip().lower()
    if lang in LANGUAGE_KEYWORDS:
        return lang
    return "all"


def _emoji_map_for_language(language: str | None) -> tuple[str, dict[str, str]]:
    scope = _normalize_language(language)
    if scope == "all":
        return scope, EMOJI_MAP
    scoped = LANGUAGE_EMOJI_MAPS.get(scope, {})
    return scope, scoped


def _pattern_for_scope(scope: str, scoped_map: dict[str, str]) -> re.Pattern | None:
    cached = _PATTERN_CACHE.get(scope)
    if cached is not None:
        return cached
    pattern = _build_pattern(scoped_map.keys())
    if pattern is not None:
        _PATTERN_CACHE[scope] = pattern
    return pattern

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def enrich_with_emojis(text: str, language: str | None = None) -> str:
    """Return *text* with emojis inserted inline after matching keywords.

    Example::

        >>> enrich_with_emojis("Heute ist tolles Wetter mit Sonne.")
        'Heute ist tolles Wetter mit Sonne ☀️.'

    If *language* is provided ("de", "en", "pl"), only that language-specific
    keyword list is used. This avoids false positives for look-alike words across
    languages.
    """
    if not text:
        return text

    scope, scoped_map = _emoji_map_for_language(language)
    pattern = _pattern_for_scope(scope, scoped_map)
    if pattern is None:
        return text

    def _replace(match: re.Match) -> str:
        word = match.group(0)
        emoji = scoped_map.get(word.lower())
        if emoji is None:
            return word
        return word + " " + emoji

    return pattern.sub(_replace, text)
