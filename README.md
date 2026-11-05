# video2mp4

Simple Windows GUI that converts DVR-exported video files to clean `.mp4`
containers so they play on WhatsApp, Google Drive, Slack, and other viewers
that choke on vendor-specific streams.

The conversion uses `ffmpeg` with stream copy (no reencoding), so it is fast
and lossless. You can optionally drop the audio track.

## Features

- Pick one or more input videos through a file dialog
- Pick the output folder (no fixed `input/` and `output/` directories)
- Choose "with audio" (copies the audio stream) or "without audio" (`-an`)
- Keeps original filenames; appends `_1`, `_2`, ... when a target already exists
- Bundled `ffmpeg.exe` (no system-wide install required for the end user)
- Optional PyInstaller build for a standalone `video2mp4.exe`

## Requirements

- Windows 10 or 11
- Python 3.11+ (only for development / running from source)
- PowerShell 5+ (for `fetch_ffmpeg.ps1`)

## Setup

Open **PowerShell** in the project root and run:

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
.\scripts\fetch_ffmpeg.ps1
```

> If PowerShell blocks the script with an ExecutionPolicy error, run it as:
> `powershell -ExecutionPolicy Bypass -File .\scripts\fetch_ffmpeg.ps1`

The last step downloads the official `ffmpeg-release-essentials` build from
[gyan.dev](https://www.gyan.dev/ffmpeg/builds/) and places `ffmpeg.exe` in
`vendor\ffmpeg\bin\`. This path is in `.gitignore` — every developer /
machine downloads its own copy.

## Running from source

From PowerShell in the project root:

```powershell
.venv\Scripts\pythonw -m src.main
```

(`pythonw` launches the GUI without a console window. Use `.venv\Scripts\python`
instead if you want to see stdout/stderr for debugging.)

## Building a standalone `.exe`

Make sure `vendor\ffmpeg\bin\ffmpeg.exe` exists first (run the setup step),
then from PowerShell:

```powershell
.venv\Scripts\pyinstaller `
    --onefile `
    --windowed `
    --name video2mp4 `
    --add-data "vendor\ffmpeg\bin\ffmpeg.exe;vendor\ffmpeg\bin" `
    src\main.py
```

The resulting binary is at `dist\video2mp4.exe`. It embeds `ffmpeg.exe` and
runs on any Windows 10/11 machine without Python installed.

## Tests

```powershell
.venv\Scripts\python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

Unit tests cover the Model and Controller layers. The View (Tkinter) is
verified manually — see smoke test below.

## Manual smoke test

1. Launch the GUI with `.venv\Scripts\pythonw -m src.main`.
2. Click **Selecionar vídeos...** and pick two DVR videos.
3. Click **Selecionar pasta...** and pick a destination folder.
4. Keep **Com áudio** selected. Click **Converter**.
5. Expected: progress bar goes from 1/2 to 2/2, then a success dialog shows
   "Convertidos 2/2 vídeos com sucesso." Two `.mp4` files land in the chosen
   folder.
6. Repeat with **Sem áudio** — the output `.mp4` has no audio track (verify
   in VLC → Tools → Codec Information or via `ffprobe`).
7. Convert the same file twice without clearing the output folder. Second
   run produces `name_1.mp4`; a third run produces `name_2.mp4`.
8. Start a batch of 3+ videos and click **Cancelar** mid-run. The currently
   processing file finishes, then the batch stops and a "Cancelado" dialog
   reports how many were completed. The file selection and audio radios are
   disabled during a running conversion.

## Architecture

MVC split:

- `src/models/` — value objects (`ConversionOptions`, `ConversionJob`),
  `filename_resolver`, `ffmpeg_locator`, `FFmpegRunner`
- `src/controllers/converter_controller.py` — orchestrates batch, emits
  progress, collects failures
- `src/views/main_window.py` — Tkinter GUI, runs the batch on a background
  thread, pumps a `queue.Queue` for progress updates
- `src/main.py` — wires everything together

## Project layout

```text
video2mp4/
├── src/                 # Python source (MVC)
├── tests/               # pytest unit tests
├── scripts/             # fetch_ffmpeg.ps1 (downloads bundled ffmpeg.exe)
├── vendor/              # bundled ffmpeg.exe (gitignored)
├── requirements.txt     # runtime deps (empty — stdlib only)
├── requirements-dev.txt # pytest, pytest-cov, pyinstaller
└── pyproject.toml       # pytest + coverage config
```

## License

This project is released under the [MIT License](LICENSE).

### ffmpeg bundling note

`scripts/fetch_ffmpeg.ps1` downloads the `ffmpeg-release-essentials` build
from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/), which is a **GPL**
build (it links against GPL components such as `libx264`). The MIT license
above applies only to the Python source code in this repository.

- Publishing / redistributing the **source** of this project: unaffected —
  the repo does not ship any ffmpeg binary (`vendor/` is gitignored).
- Distributing the **standalone `.exe`** produced by PyInstaller: the
  bundled `ffmpeg.exe` carries its GPL terms with it. If you plan to
  redistribute the `.exe`, you must comply with the ffmpeg build's license.
  See [ffmpeg.org/legal.html](https://ffmpeg.org/legal.html).

The `fetch_ffmpeg.ps1` script downloads over HTTPS but does **not** verify a
SHA-256 hash of the archive. If you need stronger supply-chain guarantees,
pin and verify the hash manually, or vendor a known-good `ffmpeg.exe` into
`vendor/ffmpeg/bin/` by other means.
