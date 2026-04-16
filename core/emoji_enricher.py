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
        "☕": ("kaffee", "kaffees"),
        "🍵": ("tee", "tees"),
        "🍺": ("bier", "biere"),
        "🍷": ("wein", "weine"),
        "🍕": ("pizza", "pizzen"),
        "🍔": ("burger", "burgers"),
        "🍣": ("sushi",),
        "🎂": ("kuchen", "torte", "torten", "geburtstag", "geburtstage"),
        "🍞": ("brot", "brote"),
        "💧": ("wasser",),
        "🍎": ("apfel", "äpfel"),
        "🍌": ("banane", "bananen"),
        "🍓": ("erdbeere", "erdbeeren"),
        "🥗": ("salat", "salate"),
        "🍫": ("schokolade", "schokoladen"),
        "🍦": ("eis",),
        "🍲": ("suppe", "suppen"),
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
        "😊": ("freude", "glück", "glücklich"),
        "😢": ("trauer", "traurig"),
        "❤️": ("liebe", "herz"),
        "😂": ("lachen",),
        "😭": ("weinen",),
        "😡": ("wut",),
        "😨": ("angst",),
        "😲": ("überraschung",),
        "🏥": ("krankenhaus", "krankenhäuser"),
        "🛒": ("supermarkt", "supermärkte"),
        "🍽️": ("restaurant", "restaurants"),
        "🏖️": ("strand", "strände", "ferien"),
        "⛰️": ("berg", "berge"),
        "🏫": ("schule", "schulen"),
        "💼": ("büro", "büros", "arbeit"),
        "⛪": ("kirche", "kirchen"),
        "🏠": ("haus", "häuser"),
        "🌳": ("park", "parks", "baum", "bäume"),
        "🏙️": ("stadt", "städte"),
        "✈️": ("flugzeug", "flugzeuge", "urlaub", "reisen"),
        "🏍️": ("motorrad", "motorräder"),
        "🚲": ("fahrrad", "fahrräder"),
        "🚀": ("rakete", "raketen"),
        "🚢": ("schiff", "schiffe"),
        "🚂": ("zug", "züge"),
        "🚗": ("auto", "autos"),
        "🚕": ("taxi", "taxis"),
        "🚌": ("bus", "busse"),
        "⚽": ("fußball", "fußbälle"),
        "🎾": ("tennis",),
        "🏊": ("schwimmen",),
        "🏃": ("laufen",),
        "🥊": ("boxen",),
        "🧘": ("yoga",),
        "⛳": ("golf",),
        "🏋️": ("sport",),
        "🦋": ("schmetterling", "schmetterlinge"),
        "🐘": ("elefant", "elefanten"),
        "🦁": ("löwe", "löwen"),
        "🐴": ("pferd", "pferde"),
        "🌸": ("blume", "blumen"),
        "🐶": ("hund", "hunde"),
        "🐱": ("katze", "katzen"),
        "🐦": ("vogel", "vögel"),
        "🐟": ("fisch", "fische"),
        "🐻": ("bär", "bären"),
        "💻": ("computer", "laptop"),
        "📱": ("handy", "handys", "telefon", "telefone"),
        "📷": ("kamera", "kameras"),
        "🎵": ("musik",),
        "📚": ("buch", "bücher"),
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
        "☕": ("coffee", "coffees"),
        "🍵": ("tea", "teas"),
        "🍺": ("beer", "beers"),
        "🍷": ("wine", "wines"),
        "🍕": ("pizza", "pizzas"),
        "🍔": ("burger", "burgers"),
        "🍣": ("sushi",),
        "🍞": ("bread", "breads"),
        "💧": ("water",),
        "🍎": ("apple", "apples"),
        "🍌": ("banana", "bananas"),
        "🍓": ("strawberry", "strawberries"),
        "🥗": ("salad", "salads"),
        "🍫": ("chocolate",),
        "🍲": ("soup", "soups"),
        "🧀": ("cheese", "cheeses"),
        "☀️": ("sun",),
        "🌧️": ("rain",),
        "❄️": ("snow",),
        "☁️": ("cloud", "clouds"),
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
        "🏥": ("hospital", "hospitals"),
        "🛒": ("supermarket", "supermarkets"),
        "🍽️": ("restaurant", "restaurants"),
        "🏖️": ("beach", "beaches", "vacation"),
        "⛰️": ("mountain", "mountains"),
        "🏫": ("school", "schools"),
        "💼": ("office", "offices", "work"),
        "⛪": ("church", "churches"),
        "🏠": ("house", "houses"),
        "🌳": ("park", "parks", "tree", "trees"),
        "🏙️": ("city", "cities"),
        "✈️": ("plane", "planes", "travel"),
        "🏍️": ("motorcycle", "motorcycles"),
        "🚲": ("bicycle", "bicycles", "bike", "bikes"),
        "🚀": ("rocket", "rockets"),
        "🚢": ("ship", "ships"),
        "🚂": ("train", "trains"),
        "🚗": ("car", "cars"),
        "🚕": ("taxi", "taxis"),
        "🚌": ("bus", "buses"),
        "🏀": ("basketball",),
        "⚽": ("soccer", "football"),
        "🎾": ("tennis",),
        "🏊": ("swimming",),
        "🏃": ("running",),
        "🥊": ("boxing",),
        "🧘": ("yoga",),
        "⛳": ("golf",),
        "🦋": ("butterfly", "butterflies"),
        "🐘": ("elephant", "elephants"),
        "🦁": ("lion", "lions"),
        "🐴": ("horse", "horses"),
        "🌸": ("flower", "flowers"),
        "🐶": ("dog", "dogs"),
        "🐱": ("cat", "cats"),
        "🐦": ("bird", "birds"),
        "🐟": ("fish",),
        "🐻": ("bear", "bears"),
        "💻": ("computer", "computers", "laptop", "laptops"),
        "📱": ("phone", "phones"),
        "📷": ("camera", "cameras"),
        "🎵": ("music",),
        "📚": ("book", "books"),
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
        "☕": ("kawa", "kawy"),
        "🍺": ("piwo",),
        "🍷": ("wino",),
        "🍕": ("pizza", "pizze"),
        "🍔": ("burger", "burgery"),
        "🍣": ("sushi",),
        "🍞": ("chleb", "chleby"),
        "💧": ("woda",),
        "🍎": ("jabłko", "jabłka", "jablko", "jablka"),
        "🍌": ("banan", "banany"),
        "🥗": ("sałatka", "sałatki", "salatka", "salatki"),
        "🍲": ("zupa", "zupy"),
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
        "🏥": ("szpital", "szpitale"),
        "🛒": ("sklep", "sklepy"),
        "🍽️": ("restaurant",),
        "🏖️": ("plaża", "plaże", "plaza", "plaze"),
        "⛰️": ("góra", "góry", "gora", "gory"),
        "🏫": ("szkoła", "szkoły", "szkola", "szkoly"),
        "💼": ("biuro", "biura", "praca"),
        "🏠": ("dom", "domy"),
        "🌳": ("park", "parki", "drzewo", "drzewa"),
        "🏙️": ("miasto", "miasta"),
        "✈️": ("samolot", "samoloty", "podróż", "podroz"),
        "🚲": ("rower", "rowery"),
        "🚢": ("statek", "statki"),
        "🚂": ("pociąg", "pociągi", "pociag", "pociagi"),
        "🚗": ("samochód", "samochody", "samochod", "samochody"),
        "🚕": ("taxi",),
        "🚌": ("bus",),
        "⚽": ("piłka", "piłki", "pilka", "pilki"),
        "🎾": ("tennis",),
        "🏊": ("pływanie", "plywanie"),
        "🏃": ("bieganie",),
        "🧘": ("yoga",),
        "⛳": ("golf",),
        "🌸": ("kwiat", "kwiaty"),
        "🐶": ("pies", "psy"),
        "🐱": ("kot", "koty"),
        "🐦": ("ptak", "ptaki"),
        "🐟": ("ryba", "ryby"),
        "💻": ("computer", "laptop"),
        "📱": ("telefon", "telefony", "telefon komórkowy", "telefony komórkowe", "telefon komorkowy", "telefony komorkowe"),
        "📷": ("kamera", "kamery"),
        "🎵": ("muzyka",),
        "📚": ("książka", "książki", "ksiazka", "ksiazki"),
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
