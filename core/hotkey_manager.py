"""
Global hotkey management via the *keyboard* library.

Registered hotkeys fire their callbacks even when the application window
is not in focus (system-wide).
"""

from __future__ import annotations

from typing import Callable

try:
    import keyboard
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "keyboard is required: pip install keyboard"
    ) from exc


class HotkeyManager:
    """Registers and manages system-wide hotkeys."""

    def __init__(self) -> None:
        # Map hotkey string -> keyboard hook id
        self._hooks: dict[str, int] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(self, hotkey: str, callback: Callable[[], None]) -> None:
        """Register (or re-register) a hotkey."""
        self.unregister(hotkey)
        hook_id = keyboard.add_hotkey(hotkey, callback, suppress=False)
        self._hooks[hotkey] = hook_id

    def unregister(self, hotkey: str) -> None:
        """Unregister a hotkey if it is currently registered."""
        if hotkey in self._hooks:
            try:
                keyboard.remove_hotkey(self._hooks[hotkey])
            except KeyError:
                pass
            del self._hooks[hotkey]

    def unregister_all(self) -> None:
        """Remove all registered hotkeys."""
        for hotkey in list(self._hooks):
            self.unregister(hotkey)
