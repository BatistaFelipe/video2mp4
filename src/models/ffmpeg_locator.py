from __future__ import annotations

import shutil
import sys
from pathlib import Path

# Exposed at module level so tests can monkeypatch it without __file__ tricks.
_MODULE_FILE = Path(__file__).resolve()


def locate_ffmpeg() -> Path:
    ffmpeg_exe = "ffmpeg.exe"

    if hasattr(sys, "_MEIPASS"):
        candidate = Path(sys._MEIPASS) / "vendor" / "ffmpeg" / "bin" / ffmpeg_exe
        if candidate.exists():
            return candidate

    project_root = _MODULE_FILE.parent.parent.parent
    bundled = project_root / "vendor" / "ffmpeg" / "bin" / ffmpeg_exe
    if bundled.exists():
        return bundled

    which_result = shutil.which("ffmpeg")
    if which_result is not None:
        return Path(which_result)

    raise FileNotFoundError(
        "ffmpeg.exe não encontrado. "
        "Coloque ffmpeg.exe em vendor/ffmpeg/bin/ ou adicione ao PATH do sistema."
    )
