# ArtTools

A desktop coding assistant (PyQt6): ask an AI to generate code, run/test it
right inside the app, review it for bugs with AI, chat freely, and monitor
system resources — all from one sidebar.

The repo ships **2 versions**:

| File | Status | Difference |
|---|---|---|
| `ArtToolsv2.py` | ✅ Recommended | Manager page only tracks CPU & RAM — stable |
| `ArtTools.py` | ⚠️ Has GPU tracking, but broken | Adds discrete GPU monitoring (via `nvidia-smi`) and integrated GPU monitoring (via Linux sysfs), but GPU load reading doesn't work correctly yet |

If you don't need GPU monitoring, always run `ArtToolsv2.py`.

## Features

| Page | Description |
|---|---|
| 💬 Code AI | Generates code on request; choose language (Python / C++ / Lua / Luau) and model (Free / Claude / DeepSeek / ChatGPT) |
| ▶ Run / Test | Runs the generated code directly — supports Python (system interpreter), C++ (compiled with `g++`), Lua/Luau (`lua` or `luau`); has a stdin box for interactive programs |
| 🔍 Error Check | Sends code to the AI for review: syntax errors, logic bugs, edge cases, performance — returns fixes with corrected code |
| 🗨 Chat Bot | Free-form chat with the AI right inside the app |
| 📊 Manager | Tracks CPU, RAM (and GPU in `ArtTools.py`), battery, and running processes |
| ❄ Effect | Background effects: Snow / Rain / Falling Leaves |
| 🔑 Settings | Enter API keys, choose the default AI model, view config info |

## Requirements

- Python 3.9+
- Python dependencies:

```bash
pip install PyQt6 requests psutil gputil
```

- For the **Run / Test** feature:
  - C++ needs `g++` available on your PATH.
  - Lua/Luau needs `lua` or `luau` on your PATH.
  - Python uses the system interpreter directly — nothing extra to install.
- For discrete NVIDIA GPU monitoring (`ArtTools.py` only): needs `nvidia-smi`
  available on your PATH (comes with the NVIDIA driver).

## Running

```bash
python ArtToolsv2.py
```

## AI Models

- **Free**: uses a public free API, no key required — quality may vary
  depending on the provider.
- **Claude / DeepSeek / ChatGPT**: requires your own API key, entered on the
  Settings page.

## Configuration

Stored at:

- Windows: `%APPDATA%\ArtTools\config.json`
- Linux/macOS: `~/.config/ArtTools/config.json`

⚠️ This file contains your API key if you've entered one — **do not
commit/share this config.json file** anywhere public.

## Notes

- The original README mistakenly listed `ArtTools.py` as the run command for
  both versions — this README fixes that: run `ArtToolsv2.py` (stable) or
  `ArtTools.py` (has GPU tracking, but it's currently broken), depending on
  your needs.
- The "Free" model (no API key needed) calls a third-party public API
  (`chateverywhere.app`) — it may stop working at any time, outside this
  repo's control; switch to a model with your own API key if it fails.
