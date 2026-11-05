from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.models.conversion_job import ConversionJob
from src.models.ffmpeg_runner import FFmpegError, FFmpegRunner


FFMPEG = Path("/usr/bin/ffmpeg")
SOURCE = Path("/input/video.dav")
DEST = Path("/output/video.mp4")


def make_job(include_audio: bool = True) -> ConversionJob:
    return ConversionJob(source=SOURCE, destination=DEST, include_audio=include_audio)


# ---------------------------------------------------------------------------
# build_command
# ---------------------------------------------------------------------------


def test_build_command_contains_y_flag():
    runner = FFmpegRunner(FFMPEG)
    cmd = runner.build_command(make_job())
    assert "-y" in cmd


def test_build_command_contains_input_flag():
    runner = FFmpegRunner(FFMPEG)
    cmd = runner.build_command(make_job())
    assert "-i" in cmd
    assert str(SOURCE) in cmd


def test_build_command_contains_vcodec_copy():
    runner = FFmpegRunner(FFMPEG)
    cmd = runner.build_command(make_job())
    assert "-vcodec" in cmd
    assert "copy" in cmd


def test_build_command_destination_is_last():
    runner = FFmpegRunner(FFMPEG)
    cmd = runner.build_command(make_job())
    assert cmd[-1] == str(DEST)


def test_build_command_starts_with_ffmpeg_path():
    runner = FFmpegRunner(FFMPEG)
    cmd = runner.build_command(make_job())
    assert cmd[0] == str(FFMPEG)


def test_build_command_include_audio_true_uses_acodec_copy():
    runner = FFmpegRunner(FFMPEG)
    cmd = runner.build_command(make_job(include_audio=True))
    assert "-acodec" in cmd
    assert "copy" in cmd
    assert "-an" not in cmd


def test_build_command_include_audio_false_uses_an():
    runner = FFmpegRunner(FFMPEG)
    cmd = runner.build_command(make_job(include_audio=False))
    assert "-an" in cmd
    assert "-acodec" not in cmd


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------


def test_run_calls_subprocess_run(monkeypatch: pytest.MonkeyPatch):
    mock_run = MagicMock(return_value=MagicMock(returncode=0, stderr=""))
    monkeypatch.setattr(subprocess, "run", mock_run)

    runner = FFmpegRunner(FFMPEG)
    job = make_job()
    runner.run(job)

    mock_run.assert_called_once()


def test_run_passes_correct_command(monkeypatch: pytest.MonkeyPatch):
    mock_run = MagicMock(return_value=MagicMock(returncode=0, stderr=""))
    monkeypatch.setattr(subprocess, "run", mock_run)

    runner = FFmpegRunner(FFMPEG)
    job = make_job()
    runner.run(job)

    call_args = mock_run.call_args
    passed_cmd = call_args[0][0]
    assert passed_cmd == runner.build_command(job)


def test_run_passes_capture_output_and_text(monkeypatch: pytest.MonkeyPatch):
    mock_run = MagicMock(return_value=MagicMock(returncode=0, stderr=""))
    monkeypatch.setattr(subprocess, "run", mock_run)

    runner = FFmpegRunner(FFMPEG)
    runner.run(make_job())

    kwargs = mock_run.call_args[1]
    assert kwargs.get("capture_output") is True
    assert kwargs.get("text") is True


def test_run_returns_none_on_success(monkeypatch: pytest.MonkeyPatch):
    mock_run = MagicMock(return_value=MagicMock(returncode=0, stderr=""))
    monkeypatch.setattr(subprocess, "run", mock_run)

    runner = FFmpegRunner(FFMPEG)
    result = runner.run(make_job())
    assert result is None


def test_run_raises_ffmpeg_error_on_nonzero(monkeypatch: pytest.MonkeyPatch):
    stderr_msg = "error: invalid codec"
    mock_run = MagicMock(return_value=MagicMock(returncode=1, stderr=stderr_msg))
    monkeypatch.setattr(subprocess, "run", mock_run)

    runner = FFmpegRunner(FFMPEG)
    with pytest.raises(FFmpegError) as exc_info:
        runner.run(make_job())

    assert stderr_msg in str(exc_info.value)


def test_ffmpeg_error_is_exception():
    err = FFmpegError("something went wrong")
    assert isinstance(err, Exception)


# ---------------------------------------------------------------------------
# timeout
# ---------------------------------------------------------------------------


def test_run_passes_timeout_when_configured(monkeypatch: pytest.MonkeyPatch):
    mock_run = MagicMock(return_value=MagicMock(returncode=0, stderr=""))
    monkeypatch.setattr(subprocess, "run", mock_run)

    runner = FFmpegRunner(FFMPEG, timeout_seconds=30.0)
    runner.run(make_job())

    kwargs = mock_run.call_args[1]
    assert kwargs.get("timeout") == 30.0


def test_run_passes_none_timeout_by_default(monkeypatch: pytest.MonkeyPatch):
    mock_run = MagicMock(return_value=MagicMock(returncode=0, stderr=""))
    monkeypatch.setattr(subprocess, "run", mock_run)

    runner = FFmpegRunner(FFMPEG)
    runner.run(make_job())

    kwargs = mock_run.call_args[1]
    assert kwargs.get("timeout") is None


def test_run_raises_ffmpeg_error_on_timeout(monkeypatch: pytest.MonkeyPatch):
    def _raise_timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd="ffmpeg", timeout=5)

    monkeypatch.setattr(subprocess, "run", _raise_timeout)

    runner = FFmpegRunner(FFMPEG, timeout_seconds=5.0)
    with pytest.raises(FFmpegError) as exc_info:
        runner.run(make_job())

    assert "tempo limite" in str(exc_info.value)
