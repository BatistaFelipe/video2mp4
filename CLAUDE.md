# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Windows Tkinter GUI that wraps `ffmpeg` to rewrap DVR-exported videos (`.dav`, `.264`, `.h265`, etc.) into clean `.mp4` containers using stream copy — no reencoding. Audio can be copied or dropped.

Legacy shell entry points (`video2mp4.sh`, `video2mp4.ps1`) are the old WSL-based implementation and are gitignored; the current app lives under `src/`.

## Commands

All commands assume the venv at `.venv/` is already created. The venv uses Windows paths (`Scripts/`), but the repo is typically driven from PowerShell.

```powershell
# First-time setup
python -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
.\scripts\fetch_ffmpeg.ps1              # downloads vendor\ffmpeg\bin\ffmpeg.exe

# Run GUI from source (no console)
.venv\Scripts\pythonw -m src.main
# Use python (not pythonw) to see stdout/stderr while debugging

# Tests with coverage gate (80% required)
.venv\Scripts\python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# Single test file / single test
.venv\Scripts\python -m pytest tests/test_converter_controller.py
.venv\Scripts\python -m pytest tests/test_converter_controller.py::test_build_jobs_handles_duplicate_stems

# Build standalone exe (requires ffmpeg.exe already present in vendor/)
.venv\Scripts\pyinstaller --onefile --windowed --name video2mp4 `
    --add-data "vendor\ffmpeg\bin\ffmpeg.exe;vendor\ffmpeg\bin" src\main.py
```

From bash/Git Bash, use forward slashes: `.venv/Scripts/python -m pytest`.

## Architecture

MVC with strict layering — the View never touches ffmpeg; the Controller never touches Tkinter.

- `src/models/` — pure, side-effect-free (or isolated) building blocks:
  - `ConversionOptions`, `ConversionJob` are `@dataclass(frozen=True)` value objects.
  - `filename_resolver.resolve_destination(source, output_dir, reserved)` is the collision-avoidance algorithm: appends `_1`, `_2`, ... when either the filesystem OR a passed-in `reserved` set already contains the target. The `reserved` set is how `ConverterController.build_jobs` prevents two inputs in the same batch from colliding before any file is written.
  - `ffmpeg_locator.locate_ffmpeg()` tries, in order: PyInstaller bundle (`sys._MEIPASS`), vendored `vendor/ffmpeg/bin/ffmpeg.exe`, then `shutil.which("ffmpeg")`. `_MODULE_FILE` is exposed at module level specifically so tests can monkeypatch the project-root lookup without `__file__` gymnastics.
  - `FFmpegRunner.build_command` is split out from `.run` to keep the subprocess invocation unit-testable. On Windows it uses `subprocess.CREATE_NO_WINDOW` so running from `pythonw` or the PyInstaller exe never flashes a cmd window. The constructor accepts an optional `timeout_seconds` — on `subprocess.TimeoutExpired` it re-raises as `FFmpegError` so partial-batch handling stays in the controller.
- `src/controllers/converter_controller.py` — orchestrates the batch. `build_jobs` plans all destinations up front (including intra-batch dedup); `run_jobs(jobs, on_progress, cancel_event=None)` executes sequentially, checks `cancel_event` between jobs (never mid-ffmpeg), and returns `list[(job, FFmpegError)]` instead of raising, so the View can surface partial failures. Cancellation is cooperative: the currently running file finishes before the loop exits.
- `src/views/main_window.py` — Tkinter UI. Conversion runs on a `threading.Thread`; the thread posts `("progress", ...)` / `("done", failures, cancelled)` tuples to a `queue.Queue`, and the main loop polls that queue via `self.after(POLL_INTERVAL_MS, ...)`. Do not call Tk widgets from the worker thread. `_set_running(True)` must be called **before** `thread.start()` and disables every action widget (convert button, file/output selection, audio radios) while enabling the Cancel button — this is what keeps a double-click or a mid-run source change from corrupting the job list.
- `src/main.py` — composition root. Locates ffmpeg (shows a Tk error dialog and exits 1 if missing), constructs `FFmpegRunner` → `ConverterController` → `MainWindow`.

### Conventions worth preserving

- Imports use `from src.<pkg>` (not relative) — `pyproject.toml` sets `pythonpath = ["."]` so pytest resolves this without an editable install. Keep running the app as a module (`python -m src.main`) rather than `python src/main.py`.
- `from __future__ import annotations` is on every file — keeps type hints lazy and `list[Path]` / `X | None` syntax usable on 3.11+ without quoting.
- UI strings are Portuguese (pt-BR) — preserve existing accents and tone when editing views/messages.
- `requirements.txt` is intentionally empty: runtime deps are stdlib only (Tkinter + subprocess). Only dev tooling goes in `requirements-dev.txt`. If you add a runtime dep, also update the PyInstaller build command.

## Testing notes

- `pyproject.toml` omits `src/views/*` and `src/main.py` from coverage — the View is verified manually (smoke test in `README.md`), so the 80% gate applies only to models + controllers. Don't add view tests just to lift the number; add them only if they catch real logic.
- Tests do not invoke real `ffmpeg`. `FFmpegRunner` and `locate_ffmpeg` are tested by monkeypatching `subprocess.run` / `_MODULE_FILE` / `shutil.which`.
- Coverage excludes `if __name__ == "__main__":` and `raise NotImplementedError` lines — don't wrap new code in those just to dodge coverage.

## ffmpeg bundling

`vendor/` is gitignored — each machine downloads its own `ffmpeg.exe` via `scripts/fetch_ffmpeg.ps1` (pulls `ffmpeg-release-essentials` from gyan.dev). The PyInstaller build embeds that same binary via `--add-data`; at runtime, `ffmpeg_locator` finds it under `sys._MEIPASS` for the frozen case.
