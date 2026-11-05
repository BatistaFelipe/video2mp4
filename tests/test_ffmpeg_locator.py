from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

import src.models.ffmpeg_locator as ffmpeg_locator_module
from src.models.ffmpeg_locator import locate_ffmpeg


def _make_ffmpeg_exe(base: Path) -> Path:
    exe = base / "vendor" / "ffmpeg" / "bin" / "ffmpeg.exe"
    exe.parent.mkdir(parents=True, exist_ok=True)
    exe.touch()
    return exe


# ---------------------------------------------------------------------------
# PyInstaller frozen (_MEIPASS) path
# ---------------------------------------------------------------------------


def test_meipass_path_returned_when_file_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    exe = _make_ffmpeg_exe(tmp_path)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    result = locate_ffmpeg()
    assert result == exe


def test_meipass_set_but_file_missing_falls_through(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    # _MEIPASS points to a dir without ffmpeg.exe; the locator must fall through
    # past the frozen branch and past the project-vendor branch, ending at the
    # shutil.which fallback.
    meipass_dir = tmp_path / "meipass"
    meipass_dir.mkdir()
    monkeypatch.setattr(sys, "_MEIPASS", str(meipass_dir), raising=False)

    # Redirect the project-vendor lookup to another empty dir so we don't
    # accidentally hit the real bundled ffmpeg.exe when it exists on disk.
    fake_module_file = tmp_path / "src" / "models" / "ffmpeg_locator.py"
    fake_module_file.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(ffmpeg_locator_module, "_MODULE_FILE", fake_module_file)

    fake_ffmpeg = tmp_path / "ffmpeg"
    fake_ffmpeg.touch()
    monkeypatch.setattr(shutil, "which", lambda _: str(fake_ffmpeg))

    result = locate_ffmpeg()
    assert result == fake_ffmpeg


# ---------------------------------------------------------------------------
# Project-root vendor path (bundled, non-frozen)
# ---------------------------------------------------------------------------


def test_project_vendor_path_returned_when_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    # Remove _MEIPASS so the frozen branch is skipped.
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)

    # Simulate __file__ being at tmp_path/src/models/ffmpeg_locator.py
    # so that parent.parent.parent == tmp_path (the fake project root).
    fake_module_file = tmp_path / "src" / "models" / "ffmpeg_locator.py"
    fake_module_file.parent.mkdir(parents=True, exist_ok=True)
    fake_module_file.touch()

    exe = _make_ffmpeg_exe(tmp_path)

    monkeypatch.setattr(ffmpeg_locator_module, "_MODULE_FILE", fake_module_file)

    result = locate_ffmpeg()
    assert result == exe


# ---------------------------------------------------------------------------
# shutil.which fallback
# ---------------------------------------------------------------------------


def test_which_fallback_when_no_bundled_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)

    # Point module file somewhere with no vendor tree.
    fake_module_file = tmp_path / "src" / "models" / "ffmpeg_locator.py"
    fake_module_file.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(ffmpeg_locator_module, "_MODULE_FILE", fake_module_file)

    fake_ffmpeg = tmp_path / "ffmpeg.exe"
    fake_ffmpeg.touch()
    monkeypatch.setattr(shutil, "which", lambda _: str(fake_ffmpeg))

    result = locate_ffmpeg()
    assert result == fake_ffmpeg


# ---------------------------------------------------------------------------
# FileNotFoundError when nothing found
# ---------------------------------------------------------------------------


def test_raises_file_not_found_when_nothing_available(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)

    fake_module_file = tmp_path / "src" / "models" / "ffmpeg_locator.py"
    fake_module_file.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(ffmpeg_locator_module, "_MODULE_FILE", fake_module_file)

    monkeypatch.setattr(shutil, "which", lambda _: None)

    with pytest.raises(FileNotFoundError):
        locate_ffmpeg()
