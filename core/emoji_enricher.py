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
# Keyword → Emoji mapping  (German + English + Polish)
# ---------------------------------------------------------------------------

EMOJI_MAP: dict[str, str] = {
    # Essen & Trinken / Food & Drinks
    "kaffee": "☕",
    "coffee": "☕",
    "tee": "🍵",
    "tea": "🍵",
    "bier": "🍺",
    "beer": "🍺",
    "wein": "🍷",
    "wine": "🍷",
    "pizza": "🍕",
    "burger": "🍔",
    "sushi": "🍣",
    "kuchen": "🎂",
    "torte": "🎂",
    "brot": "🍞",
    "bread": "🍞",
    "wasser": "💧",
    "water": "💧",
    "apfel": "🍎",
    "apple": "🍎",
    "banane": "🍌",
    "banana": "🍌",
    "erdbeere": "🍓",
    "strawberry": "🍓",
    "salat": "🥗",
    "salad": "🥗",
    "schokolade": "🍫",
    "chocolate": "🍫",
    "eis": "🍦",
    "suppe": "🍲",
    "soup": "🍲",
    "käse": "🧀",
    "cheese": "🧀",
    "kawa": "☕",
    "piwo": "🍺",
    "wino": "🍷",
    "chleb": "🍞",
    "woda": "💧",
    "jabłko": "🍎",
    "jablko": "🍎",
    "banan": "🍌",
    "sałatka": "🥗",
    "salatka": "🥗",
    "zupa": "🍲",
    "ser": "🧀",
    # Wetter / Weather
    "sonne": "☀️",
    "sun": "☀️",
    "sonnig": "☀️",
    "regen": "🌧️",
    "rain": "🌧️",
    "regnerisch": "🌧️",
    "schnee": "❄️",
    "snow": "❄️",
    "wolke": "☁️",
    "wolken": "☁️",
    "cloud": "☁️",
    "gewitter": "⛈️",
    "thunderstorm": "⛈️",
    "wind": "💨",
    "nebel": "🌫️",
    "fog": "🌫️",
    "regenbogen": "🌈",
    "rainbow": "🌈",
    "blitz": "⚡",
    "lightning": "⚡",
    "słońce": "☀️",
    "slonce": "☀️",
    "deszcz": "🌧️",
    "śnieg": "❄️",
    "snieg": "❄️",
    "chmura": "☁️",
    "burza": "⛈️",
    "wiatr": "💨",
    "mgła": "🌫️",
    "mgla": "🌫️",
    "tęcza": "🌈",
    "tecza": "🌈",
    "błyskawica": "⚡",
    "blyskawica": "⚡",
    # Emotionen / Emotions
    "freude": "😊",
    "glück": "😊",
    "happy": "😊",
    "trauer": "😢",
    "traurig": "😢",
    "sad": "😢",
    "liebe": "❤️",
    "love": "❤️",
    "lachen": "😂",
    "laugh": "😂",
    "weinen": "😭",
    "cry": "😭",
    "wut": "😡",
    "angry": "😡",
    "angst": "😨",
    "fear": "😨",
    "überraschung": "😲",
    "surprise": "😲",
    "radość": "😊",
    "radosc": "😊",
    "smutek": "😢",
    "miłość": "❤️",
    "milosc": "❤️",
    "złość": "😡",
    "zlosc": "😡",
    "strach": "😨",
    # Orte & Gebäude / Places & Buildings
    "krankenhaus": "🏥",
    "hospital": "🏥",
    "supermarkt": "🛒",
    "supermarket": "🛒",
    "restaurant": "🍽️",
    "strand": "🏖️",
    "beach": "🏖️",
    "berg": "⛰️",
    "mountain": "⛰️",
    "schule": "🏫",
    "school": "🏫",
    "büro": "💼",
    "office": "💼",
    "kirche": "⛪",
    "church": "⛪",
    "haus": "🏠",
    "house": "🏠",
    "park": "🌳",
    "stadt": "🏙️",
    "city": "🏙️",
    "szpital": "🏥",
    "sklep": "🛒",
    "plaża": "🏖️",
    "plaza": "🏖️",
    "góra": "⛰️",
    "gora": "⛰️",
    "szkoła": "🏫",
    "szkola": "🏫",
    "biuro": "💼",
    "dom": "🏠",
    "miasto": "🏙️",
    # Transport
    "flugzeug": "✈️",
    "motorrad": "🏍️",
    "motorcycle": "🏍️",
    "fahrrad": "🚲",
    "bicycle": "🚲",
    "bike": "🚲",
    "rakete": "🚀",
    "rocket": "🚀",
    "schiff": "🚢",
    "ship": "🚢",
    "zug": "🚂",
    "train": "🚂",
    "auto": "🚗",
    "car": "🚗",
    "taxi": "🚕",
    "bus": "🚌",
    "plane": "✈️",
    "samolot": "✈️",
    "rower": "🚲",
    "statek": "🚢",
    "pociąg": "🚂",
    "pociag": "🚂",
    "samochód": "🚗",
    "samochod": "🚗",
    # Sport
    "basketball": "🏀",
    "fußball": "⚽",
    "soccer": "⚽",
    "football": "⚽",
    "tennis": "🎾",
    "schwimmen": "🏊",
    "swimming": "🏊",
    "laufen": "🏃",
    "running": "🏃",
    "boxen": "🥊",
    "boxing": "🥊",
    "yoga": "🧘",
    "golf": "⛳",
    "sport": "🏋️",
    "piłka": "⚽",
    "pilka": "⚽",
    "pływanie": "🏊",
    "plywanie": "🏊",
    "bieganie": "🏃",
    # Natur & Tiere / Nature & Animals
    "schmetterling": "🦋",
    "butterfly": "🦋",
    "elefant": "🐘",
    "elephant": "🐘",
    "löwe": "🦁",
    "lion": "🦁",
    "pferd": "🐴",
    "horse": "🐴",
    "baum": "🌳",
    "tree": "🌳",
    "blume": "🌸",
    "flower": "🌸",
    "hund": "🐶",
    "dog": "🐶",
    "katze": "🐱",
    "cat": "🐱",
    "vogel": "🐦",
    "bird": "🐦",
    "fisch": "🐟",
    "fish": "🐟",
    "bär": "🐻",
    "bear": "🐻",
    "drzewo": "🌳",
    "kwiat": "🌸",
    "pies": "🐶",
    "kot": "🐱",
    "ptak": "🐦",
    "ryba": "🐟",
    # Technik / Technology
    "computer": "💻",
    "laptop": "💻",
    "handy": "📱",
    "telefon": "📱",
    "phone": "📱",
    "kamera": "📷",
    "camera": "📷",
    "musik": "🎵",
    "music": "🎵",
    "buch": "📚",
    "book": "📚",
    "fernsehen": "📺",
    "television": "📺",
    "telefon komórkowy": "📱",
    "telefon komorkowy": "📱",
    "książka": "📚",
    "ksiazka": "📚",
    "muzyka": "🎵",
    # Allgemein / General
    "geburtstag": "🎂",
    "birthday": "🎂",
    "urlaub": "✈️",
    "ferien": "🏖️",
    "vacation": "🏖️",
    "feuer": "🔥",
    "fire": "🔥",
    "herz": "❤️",
    "heart": "❤️",
    "stern": "⭐",
    "star": "⭐",
    "geld": "💰",
    "money": "💰",
    "schlafen": "😴",
    "sleep": "😴",
    "nacht": "🌙",
    "night": "🌙",
    "morgen": "🌅",
    "morning": "🌅",
    "party": "🎉",
    "danke": "🙏",
    "thanks": "🙏",
    "hallo": "👋",
    "hello": "👋",
    "tschüss": "👋",
    "bye": "👋",
    "reisen": "✈️",
    "travel": "✈️",
    "arbeit": "💼",
    "work": "💼",
    "dzień dobry": "👋",
    "dzien dobry": "👋",
    "cześć": "👋",
    "czesc": "👋",
    "dziękuję": "🙏",
    "dziekuje": "🙏",
    "podróż": "✈️",
    "podroz": "✈️",
    "praca": "💼",
}

LANGUAGE_KEYWORDS: dict[str, set[str]] = {
    "de": {
        "kaffee", "tee", "bier", "wein", "pizza", "burger", "sushi", "kuchen", "torte", "brot", "wasser",
        "apfel", "banane", "erdbeere", "salat", "schokolade", "eis", "suppe", "käse",
        "sonne", "sonnig", "regen", "regnerisch", "schnee", "wolke", "wolken", "gewitter", "wind",
        "nebel", "regenbogen", "blitz", "freude", "glück", "trauer", "traurig", "liebe", "lachen",
        "weinen", "wut", "angst", "überraschung", "krankenhaus", "supermarkt", "restaurant", "strand",
        "berg", "schule", "büro", "kirche", "haus", "park", "stadt", "flugzeug", "motorrad",
        "fahrrad", "rakete", "schiff", "zug", "auto", "taxi", "bus", "fußball", "tennis", "schwimmen",
        "laufen", "boxen", "yoga", "golf", "sport", "schmetterling", "elefant", "löwe", "pferd",
        "baum", "blume", "hund", "katze", "vogel", "fisch", "bär", "computer", "laptop", "handy",
        "telefon", "kamera", "musik", "buch", "fernsehen", "geburtstag", "urlaub", "ferien", "feuer",
        "herz", "stern", "geld", "schlafen", "nacht", "morgen", "party", "danke", "hallo", "tschüss",
        "reisen", "arbeit"
    },
    "en": {
        "coffee", "tea", "beer", "wine", "pizza", "burger", "sushi", "bread", "water", "apple",
        "banana", "strawberry", "salad", "chocolate", "soup", "cheese", "sun", "rain", "snow", "cloud",
        "thunderstorm", "fog", "rainbow", "lightning", "happy", "sad", "love", "laugh", "cry", "angry",
        "fear", "surprise", "hospital", "supermarket", "restaurant", "beach", "mountain", "school", "office",
        "church", "house", "park", "city", "motorcycle", "bicycle", "bike", "rocket", "ship", "train",
        "car", "taxi", "bus", "plane", "basketball", "soccer", "football", "tennis", "swimming", "running",
        "boxing", "yoga", "golf", "butterfly", "elephant", "lion", "horse", "tree", "flower", "dog", "cat",
        "bird", "fish", "bear", "computer", "laptop", "phone", "camera", "music", "book", "television",
        "birthday", "vacation", "fire", "heart", "star", "money", "sleep", "night", "morning", "party",
        "thanks", "hello", "bye", "travel", "work"
    },
    "pl": {
        "kawa", "piwo", "wino", "pizza", "burger", "sushi", "chleb", "woda", "jabłko", "jablko", "banan",
        "sałatka", "salatka", "zupa", "ser", "słońce", "slonce", "deszcz", "śnieg", "snieg", "chmura",
        "burza", "wiatr", "mgła", "mgla", "tęcza", "tecza", "błyskawica", "blyskawica", "radość", "radosc",
        "smutek", "miłość", "milosc", "złość", "zlosc", "strach", "szpital", "sklep", "restaurant", "plaża",
        "plaza", "góra", "gora", "szkoła", "szkola", "biuro", "dom", "park", "miasto", "samolot", "rower",
        "statek", "pociąg", "pociag", "samochód", "samochod", "taxi", "bus", "piłka", "pilka", "tennis",
        "pływanie", "plywanie", "bieganie", "yoga", "golf", "drzewo", "kwiat", "pies", "kot", "ptak", "ryba",
        "computer", "laptop", "telefon", "telefon komórkowy", "telefon komorkowy", "kamera", "muzyka", "książka",
        "ksiazka", "birthday", "fire", "heart", "star", "money", "sleep", "night", "morning", "party",
        "dzień dobry", "dzien dobry", "cześć", "czesc", "dziękuję", "dziekuje", "podróż", "podroz", "praca"
    },
}

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
    keywords = LANGUAGE_KEYWORDS.get(scope, set())
    scoped = {key: EMOJI_MAP[key] for key in keywords if key in EMOJI_MAP}
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
