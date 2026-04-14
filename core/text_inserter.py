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

import time

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


def insert_text(text: str) -> None:
    """Paste *text* into the currently focused application."""
    if not text:
        return

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


def press_enter() -> None:
    """Press the Enter key in the currently focused application."""
    pyautogui.press("enter")


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
