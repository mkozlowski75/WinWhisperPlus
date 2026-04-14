"""
Text insertion – types transcribed text into the currently active window
using the Windows clipboard for reliable Unicode support.

Strategy
--------
1. Save the existing clipboard content.
2. Put the new text on the clipboard.
3. Send Ctrl+V to the foreground window.
4. Restore the previous clipboard content (best-effort).
"""

from __future__ import annotations

import threading
import time

from core.live_text import split_text_update

try:
    import win32clipboard
    import win32con
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "pywin32 is required: pip install pywin32"
    ) from exc

try:
    import pyautogui
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "pyautogui is required: pip install pyautogui"
    ) from exc

_PASTE_DELAY = 0.05   # seconds between clipboard write and Ctrl+V
_DELETE_DELAY = 0.01
_clipboard_lock = threading.RLock()


def insert_text(text: str) -> None:
    """Paste *text* into the currently focused application."""
    if not text:
        return

    with _clipboard_lock:
        _paste_text(text)


def replace_text(previous_text: str, new_text: str) -> None:
    """Replace the most recently inserted text block with *new_text*."""
    with _clipboard_lock:
        delete_count, insert_suffix = split_text_update(previous_text, new_text)
        if delete_count > 0:
            pyautogui.press("backspace", presses=delete_count, interval=_DELETE_DELAY)
        if insert_suffix:
            _paste_text(insert_suffix)


def press_enter() -> None:
    """Press the Enter key in the currently focused application."""
    with _clipboard_lock:
        time.sleep(0.1)  # Small delay to ensure focus
        pyautogui.press("enter")
        time.sleep(0.1)  # Small delay after pressing


def _paste_text(text: str) -> None:
    previous = _get_clipboard()
    try:
        _set_clipboard(text)
        time.sleep(_PASTE_DELAY)
        pyautogui.hotkey("ctrl", "v")
    finally:
        # Restore previous clipboard (best-effort, small delay)
        time.sleep(_PASTE_DELAY)
        if previous is not None:
            _set_clipboard(previous)


# ------------------------------------------------------------------
# Clipboard helpers
# ------------------------------------------------------------------

def _get_clipboard() -> str | None:
    try:
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
            data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
        else:
            data = None
    except Exception:  # noqa: BLE001
        data = None
    finally:
        try:
            win32clipboard.CloseClipboard()
        except Exception:  # noqa: BLE001
            pass
    return data


def _set_clipboard(text: str) -> None:
    try:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
    finally:
        try:
            win32clipboard.CloseClipboard()
        except Exception:  # noqa: BLE001
            pass
