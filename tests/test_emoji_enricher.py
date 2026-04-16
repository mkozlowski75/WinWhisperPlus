"""Tests for core/emoji_enricher.py"""

import pytest

from core.emoji_enricher import enrich_with_emojis, EMOJI_MAP


class TestEnrichWithEmojis:

    def test_known_keyword_is_enriched_inline(self):
        result = enrich_with_emojis("Ich trinke Kaffee am Morgen.")
        assert "Kaffee ☕" in result

    def test_case_insensitive_matching(self):
        lower = enrich_with_emojis("kaffee ist gut.")
        upper = enrich_with_emojis("KAFFEE ist gut.")
        mixed = enrich_with_emojis("Kaffee ist gut.")
        assert "kaffee ☕" in lower
        assert "KAFFEE ☕" in upper
        assert "Kaffee ☕" in mixed

    def test_no_match_returns_text_unchanged(self):
        text = "Keine bekannten Schlüsselwörter hier drin."
        assert enrich_with_emojis(text) == text

    def test_multiple_keywords_in_sentence(self):
        result = enrich_with_emojis("Sonne und Regen am Strand.")
        assert "Sonne ☀️" in result
        assert "Regen 🌧️" in result
        assert "Strand 🏖️" in result

    def test_word_boundary_no_partial_match(self):
        # "haus" must not trigger inside "krankenhaus"
        result = enrich_with_emojis("Ich gehe ins Krankenhaus.")
        assert "Krankenhaus 🏥" in result
        # After enrichment "haus" should not appear separately as a standalone match
        # (the word "haus" only appears as part of "Krankenhaus")
        parts = result.split()
        emojis_after_haus = [
            parts[i + 1]
            for i, p in enumerate(parts)
            if p.lower() == "haus" and i + 1 < len(parts)
        ]
        assert emojis_after_haus == [], "standalone 'haus' emoji must not appear inside 'Krankenhaus'"

    def test_word_boundary_standalone_haus(self):
        result = enrich_with_emojis("Das ist mein Haus.")
        assert "Haus 🏠" in result

    def test_empty_string_returns_empty(self):
        assert enrich_with_emojis("") == ""

    def test_text_with_only_whitespace_is_unchanged(self):
        assert enrich_with_emojis("   ") == "   "

    def test_emoji_map_has_entries(self):
        assert len(EMOJI_MAP) > 50

    def test_english_keyword_is_enriched(self):
        result = enrich_with_emojis("I love coffee in the morning.")
        assert "coffee ☕" in result

    def test_original_word_casing_is_preserved(self):
        result = enrich_with_emojis("PIZZA bitte.")
        assert result.startswith("PIZZA 🍕")

    def test_supermarkt_not_split_into_markt(self):
        # "Supermarkt" should not trigger a spurious match on any sub-word
        result = enrich_with_emojis("Ich gehe zum Supermarkt.")
        assert "Supermarkt 🛒" in result

    def test_polish_keywords_are_enriched(self):
        result = enrich_with_emojis("Kawa, szpital i deszcz.")
        assert "Kawa ☕" in result
        assert "szpital 🏥" in result
        assert "deszcz 🌧️" in result

    def test_polish_diacritics_and_case_insensitive_matching(self):
        result = enrich_with_emojis("SŁOŃCE, MiŁoŚĆ i DZIĘKUJĘ.")
        assert "SŁOŃCE ☀️" in result
        assert "MiŁoŚĆ ❤️" in result
        assert "DZIĘKUJĘ 🙏" in result

    def test_language_scope_avoids_false_friend_bier_in_polish(self):
        polish_result = enrich_with_emojis("Ja bier książkę.", language="pl")
        assert "bier 🍺" not in polish_result.lower()

        german_result = enrich_with_emojis("Ich trinke Bier.", language="de")
        assert "Bier 🍺" in german_result

    def test_language_scope_uses_only_requested_language(self):
        # English scope should not apply Polish-only keyword map entries.
        english_scoped = enrich_with_emojis("Kawa i coffee.", language="en")
        assert "Kawa ☕" not in english_scoped
        assert "coffee ☕" in english_scoped

        polish_scoped = enrich_with_emojis("Kawa i coffee.", language="pl")
        assert "Kawa ☕" in polish_scoped
        assert "coffee ☕" not in polish_scoped

    def test_german_plural_keywords_are_enriched(self):
        result = enrich_with_emojis("Supermärkte und Häuser sind heute voll.", language="de")
        assert "Supermärkte 🛒" in result
        assert "Häuser 🏠" in result

    def test_english_plural_keywords_are_enriched(self):
        result = enrich_with_emojis("Hospitals and supermarkets are busy.", language="en")
        assert "Hospitals 🏥" in result
        assert "supermarkets 🛒" in result

    def test_polish_plural_keywords_are_enriched(self):
        result = enrich_with_emojis("Szpitale i sklepy są otwarte.", language="pl")
        assert "Szpitale 🏥" in result
        assert "sklepy 🛒" in result
