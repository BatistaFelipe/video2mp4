from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

from src.models.conversion_job import ConversionJob
from src.models.conversion_options import ConversionOptions
from src.models.ffmpeg_runner import FFmpegError, FFmpegRunner
from src.models.filename_resolver import resolve_destination


class ConverterController:
    def __init__(self, runner: FFmpegRunner) -> None:
        self._runner = runner

    def build_jobs(
        self, sources: list[Path], options: ConversionOptions
    ) -> list[ConversionJob]:
        reserved: set[Path] = set()
        jobs: list[ConversionJob] = []

        for source in sources:
            destination = resolve_destination(source, options.output_dir, reserved)
            reserved.add(destination)
            jobs.append(ConversionJob(source, destination, options.include_audio))

        return jobs

    def run_jobs(
        self,
        jobs: list[ConversionJob],
        on_progress: Callable[[int, int, str], None],
        cancel_event: threading.Event | None = None,
    ) -> list[tuple[ConversionJob, FFmpegError]]:
        total = len(jobs)
        failures: list[tuple[ConversionJob, FFmpegError]] = []

        for index, job in enumerate(jobs):
            if cancel_event is not None and cancel_event.is_set():
                break
            on_progress(index + 1, total, job.source.name)
            try:
                self._runner.run(job)
            except FFmpegError as err:
                failures.append((job, err))

        return failures
