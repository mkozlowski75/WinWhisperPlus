"""Tests for live transcription text helpers."""

from core.live_text import extract_enter_command, merge_live_tail, split_text_update, stable_partial_text


def test_stable_partial_text_returns_first_text_when_no_previous() -> None:
    stable = stable_partial_text("", "hallo welt")

    assert stable == "hallo welt"


def test_stable_partial_text_returns_common_prefix() -> None:
    stable = stable_partial_text(
        "hallo welt dies ist",
        "hallo welt dies ist ein test",
    )

    assert stable == "hallo welt dies ist"


def test_stable_partial_text_stops_at_first_difference() -> None:
    stable = stable_partial_text(
        "hallo welt dies ist",
        "hallo du dies ist",
    )

    assert stable == "hallo"


def test_extract_enter_command_detects_trailing_command() -> None:
    text, should_press_enter = extract_enter_command("Hallo Welt enter")

    assert text == "Hallo Welt"
    assert should_press_enter is True


def test_extract_enter_command_ignores_normal_text() -> None:
    text, should_press_enter = extract_enter_command("Hallo Welt")

    assert text == "Hallo Welt"
    assert should_press_enter is False


def test_split_text_update_appends_only_new_suffix() -> None:
    delete_count, insert_suffix = split_text_update("Hallo Welt", "Hallo Welt heute")

    assert delete_count == 0
    assert insert_suffix == " heute"


def test_split_text_update_replaces_only_changed_suffix() -> None:
    delete_count, insert_suffix = split_text_update("Hallo Wekt", "Hallo Welt heute")

    assert delete_count == 2
    assert insert_suffix == "lt heute"


def test_split_text_update_replaces_entire_text_when_no_common_prefix() -> None:
    delete_count, insert_suffix = split_text_update("abc", "xyz")

    assert delete_count == 3
    assert insert_suffix == "xyz"


def test_merge_live_tail_commits_shifted_prefix() -> None:
    committed, tail, rendered = merge_live_tail(
        committed_text="",
        previous_tail_text="hallo welt dies ist",
        new_tail_text="welt dies ist ein test",
    )

    assert committed == "hallo"
    assert tail == "welt dies ist ein test"
    assert rendered == "hallo welt dies ist ein test"


def test_merge_live_tail_replaces_tail_on_small_overlap() -> None:
    committed, tail, rendered = merge_live_tail(
        committed_text="hallo",
        previous_tail_text="welt dise ist",
        new_tail_text="welt dies ist ein test",
    )

    assert committed == "hallo"
    assert tail == "welt dies ist ein test"
    assert rendered == "hallo welt dies ist ein test"