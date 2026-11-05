from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from src.models.conversion_job import ConversionJob

CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


class FFmpegError(Exception):
    pass


class FFmpegRunner:
    def __init__(
        self, ffmpeg_path: Path, timeout_seconds: float | None = None
    ) -> None:
        self._ffmpeg_path = ffmpeg_path
        self._timeout_seconds = timeout_seconds

    def build_command(self, job: ConversionJob) -> list[str]:
        audio_args = ["-acodec", "copy"] if job.include_audio else ["-an"]
        return [
            str(self._ffmpeg_path),
            "-y",
            "-i",
            str(job.source),
            "-vcodec",
            "copy",
            *audio_args,
            str(job.destination),
        ]

    def run(self, job: ConversionJob) -> None:
        cmd = self.build_command(job)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=CREATE_NO_WINDOW,
                timeout=self._timeout_seconds,
            )
        except subprocess.TimeoutExpired as err:
            raise FFmpegError(
                f"ffmpeg excedeu o tempo limite de {self._timeout_seconds}s "
                f"ao processar {job.source.name}"
            ) from err
        if result.returncode != 0:
            raise FFmpegError(result.stderr)
