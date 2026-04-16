# MyWhisper

Ein Windows-Tool zur lokalen Spracherkennung auf Basis von OpenAI Whisper.  
A Windows speech-recognition tool powered by OpenAI Whisper running entirely locally.

## Features

- 🎤 **Speech-to-Text** – Converts microphone input to text using OpenAI Whisper (local, no cloud).
- 🌍 **Language support** – German (Deutsch), Polish (Polski), English.
- ⌨️ **System-wide hotkeys** – Configurable hotkeys to start/stop recording and cycle languages.
- 📋 **Auto-insert** – Transcribed text is automatically pasted into the currently active input field.
- ⚡ **Live mode** – Optional near real-time transcription inserts stable partial text while you are still speaking.
- 📊 **Usage statistics** – Tracks successful sessions and shows count/total/average recording duration per day, week, and month.
- 🎛️ **Microphone selection** – Choose from all connected input devices.
- 🔔 **System tray** – Runs silently in the background with a tray icon and context menu.
- ⚙️ **Settings GUI** – Configure hotkeys, language, microphone and Whisper model size.

## Default Hotkeys

| Action                     | Default shortcut    |
|----------------------------|---------------------|
| Start / stop recording     | `Alt + Shift + R`   |
| Cycle language             | `Alt + Shift + S`   |

Both hotkeys are fully configurable in the settings dialog.

## Requirements

- Windows 10 64-bit or newer
- Python 3.10+
- NVIDIA GPU recommended (for faster transcription)

## Installation

```bash
pip install -r requirements.txt
```

> **Note:** `torch` may require a separate CUDA-enabled install.  
> See [pytorch.org](https://pytorch.org/get-started/locally/) for the right command for your system.

## Usage

```bash
python main.py
```

The application starts minimised to the system tray.  
Double-click the tray icon or use the hotkey to start/stop recording.

## Configuration

Click **Einstellungen…** in the tray menu to open the settings dialog where you can:

- Change hotkeys by clicking the field and pressing the desired key combination.
- Select the default language (Deutsch / Polski / English).
- Choose a specific microphone from the dropdown.
- Select the Whisper model size (`tiny` → `large`; larger = more accurate but slower).
- Enable live transcription if you want stable partial text to be inserted during an active recording.

## Live Transcription

The optional live mode keeps the current push-to-talk workflow, but starts transcribing overlapping audio chunks during the recording.

- Stable partial text is inserted while the recording is still running.
- When you stop recording, the final full transcription replaces the live partial text block.
- Spoken `enter` is only executed on the final result so partial hypotheses do not trigger unwanted line breaks.
- For the best latency, `tiny` or `base` are recommended in live mode.

Settings are saved to `%APPDATA%\MyWhisper\settings.json`.
Statistics are saved to `%APPDATA%\MyWhisper\statistics.json`.

## Running Tests

```bash
pip install -r requirements-dev.txt
pytest tests/
```

## Architecture

```
MyWhisper/
├── main.py                  # Entry point
├── app.py                   # Application orchestrator
├── config/
│   └── settings.py          # Settings persistence (JSON)
├── core/
│   ├── recorder.py          # Microphone capture (sounddevice)
│   ├── transcriber.py       # Whisper inference wrapper
│   ├── text_inserter.py     # Clipboard-based text paste
│   └── hotkey_manager.py    # System-wide hotkeys (keyboard lib)
├── gui/
│   ├── tray_icon.py         # System tray icon & menu (PyQt6)
│   ├── status_window.py     # Floating status indicator
│   └── settings_window.py   # Settings dialog
└── tests/
    ├── test_settings.py
    ├── test_recorder.py
    ├── test_transcriber.py
    └── test_hotkey_manager.py
```