"""Helpers for deriving stable live transcription text."""

from __future__ import annotations


def stable_partial_text(previous_text: str, current_text: str) -> str:
    """Return the stable common word-prefix between consecutive hypotheses."""
    if not previous_text.strip():
        return current_text.strip()

    previous_words = previous_text.split()
    current_words = current_text.split()
    prefix_len = 0

    while prefix_len < len(previous_words) and prefix_len < len(current_words):
        if previous_words[prefix_len].lower() != current_words[prefix_len].lower():
            break
        prefix_len += 1

    return " ".join(current_words[:prefix_len]).strip()


def split_text_update(previous_text: str, new_text: str) -> tuple[int, str]:
    """Return how many trailing chars to delete and which suffix to insert."""
    shared_prefix_len = 0
    max_prefix_len = min(len(previous_text), len(new_text))

    while shared_prefix_len < max_prefix_len:
        if previous_text[shared_prefix_len] != new_text[shared_prefix_len]:
            break
        shared_prefix_len += 1

    delete_count = len(previous_text) - shared_prefix_len
    insert_suffix = new_text[shared_prefix_len:]
    return delete_count, insert_suffix


def merge_live_tail(
    committed_text: str,
    previous_tail_text: str,
    new_tail_text: str,
    min_overlap_words: int = 1,
) -> tuple[str, str, str]:
    """Merge a new rolling-tail hypothesis into committed+tail text state."""
    new_tail = " ".join(new_tail_text.split()).strip()
    previous_tail = " ".join(previous_tail_text.split()).strip()
    committed = " ".join(committed_text.split()).strip()

    if not previous_tail:
        return committed, new_tail, _join_parts(committed, new_tail)

    previous_words = previous_tail.split()
    new_words = new_tail.split()
    overlap = _suffix_prefix_word_overlap(previous_words, new_words)

    if overlap >= min_overlap_words:
        commit_words = previous_words[:-overlap]
        if commit_words:
            commit_segment = " ".join(commit_words)
            committed = _join_parts(committed, commit_segment)
        tail = new_tail
    else:
        # Small/no overlap usually means a correction in the editable tail.
        tail = new_tail

    return committed, tail, _join_parts(committed, tail)


def _suffix_prefix_word_overlap(previous_words: list[str], new_words: list[str]) -> int:
    max_overlap = min(len(previous_words), len(new_words))
    for overlap in range(max_overlap, 0, -1):
        prev_slice = [_normalize_word(w) for w in previous_words[-overlap:]]
        new_slice = [_normalize_word(w) for w in new_words[:overlap]]
        if prev_slice == new_slice:
            return overlap
    return 0


def _normalize_word(word: str) -> str:
    """Lowercase and strip punctuation for overlap comparison."""
    return "".join(c.lower() for c in word if c.isalpha() or c.isdigit())


def _join_parts(left: str, right: str) -> str:
    if left and right:
        return f"{left} {right}".strip()
    return left or right


def extract_enter_command(text: str) -> tuple[str, bool]:
    """Split a trailing spoken 'enter' command from text."""
    words = text.strip().split()
    if not words:
        return "", False

    last_word = "".join(char for char in words[-1] if char.isalnum() or char == "_").lower()
    if last_word != "enter":
        return text.strip(), False

    return " ".join(words[:-1]).strip(), True