from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

import pytest

from src.controllers.converter_controller import ConverterController
from src.models.conversion_job import ConversionJob
from src.models.conversion_options import ConversionOptions
from src.models.ffmpeg_runner import FFmpegError


class FakeRunner:
    def __init__(self, fail_on_indices: set[int] | None = None) -> None:
        self.calls: list[ConversionJob] = []
        self._fail_on_indices: set[int] = fail_on_indices or set()

    def run(self, job: ConversionJob) -> None:
        index = len(self.calls)
        self.calls.append(job)
        if index in self._fail_on_indices:
            raise FFmpegError(f"simulated failure at index {index}")


def make_options(tmp_path: Path, include_audio: bool = True) -> ConversionOptions:
    return ConversionOptions(output_dir=tmp_path, include_audio=include_audio)


# ---------------------------------------------------------------------------
# build_jobs
# ---------------------------------------------------------------------------


def test_build_jobs_returns_one_job_per_source(tmp_path: Path):
    sources = [Path("/input/a.dav"), Path("/input/b.dav")]
    opts = make_options(tmp_path)
    ctrl = ConverterController(FakeRunner())
    jobs = ctrl.build_jobs(sources, opts)
    assert len(jobs) == len(sources)


def test_build_jobs_sources_in_order(tmp_path: Path):
    sources = [Path("/input/a.dav"), Path("/input/b.dav"), Path("/input/c.dav")]
    opts = make_options(tmp_path)
    ctrl = ConverterController(FakeRunner())
    jobs = ctrl.build_jobs(sources, opts)
    assert [j.source for j in jobs] == sources


def test_build_jobs_destinations_use_output_dir(tmp_path: Path):
    sources = [Path("/input/clip.dav")]
    opts = make_options(tmp_path)
    ctrl = ConverterController(FakeRunner())
    jobs = ctrl.build_jobs(sources, opts)
    assert jobs[0].destination.parent == tmp_path


def test_build_jobs_carries_include_audio(tmp_path: Path):
    sources = [Path("/input/clip.dav")]
    opts = make_options(tmp_path, include_audio=False)
    ctrl = ConverterController(FakeRunner())
    jobs = ctrl.build_jobs(sources, opts)
    assert jobs[0].include_audio is False


def test_build_jobs_unique_destinations_for_same_stem(tmp_path: Path):
    sources = [Path("/dir1/video.dav"), Path("/dir2/video.dav")]
    opts = make_options(tmp_path)
    ctrl = ConverterController(FakeRunner())
    jobs = ctrl.build_jobs(sources, opts)
    destinations = [j.destination for j in jobs]
    assert len(set(destinations)) == 2


def test_build_jobs_same_stem_uses_incrementing_suffix(tmp_path: Path):
    sources = [
        Path("/dir1/video.dav"),
        Path("/dir2/video.dav"),
        Path("/dir3/video.dav"),
    ]
    opts = make_options(tmp_path)
    ctrl = ConverterController(FakeRunner())
    jobs = ctrl.build_jobs(sources, opts)
    assert jobs[0].destination.name == "video.mp4"
    assert jobs[1].destination.name == "video_1.mp4"
    assert jobs[2].destination.name == "video_2.mp4"


def test_build_jobs_empty_sources(tmp_path: Path):
    opts = make_options(tmp_path)
    ctrl = ConverterController(FakeRunner())
    jobs = ctrl.build_jobs([], opts)
    assert jobs == []


def test_build_jobs_destinations_are_mp4(tmp_path: Path):
    sources = [Path("/input/clip.dav")]
    opts = make_options(tmp_path)
    ctrl = ConverterController(FakeRunner())
    jobs = ctrl.build_jobs(sources, opts)
    assert jobs[0].destination.suffix == ".mp4"


# ---------------------------------------------------------------------------
# run_jobs
# ---------------------------------------------------------------------------


def test_run_jobs_calls_on_progress_before_each_job(tmp_path: Path):
    sources = [Path("/input/a.dav"), Path("/input/b.dav")]
    opts = make_options(tmp_path)
    ctrl = ConverterController(FakeRunner())
    jobs = ctrl.build_jobs(sources, opts)

    progress_calls: list[tuple[int, int, str]] = []

    def on_progress(current: int, total: int, name: str) -> None:
        progress_calls.append((current, total, name))

    ctrl.run_jobs(jobs, on_progress)

    assert len(progress_calls) == 2
    assert progress_calls[0] == (1, 2, "a.dav")
    assert progress_calls[1] == (2, 2, "b.dav")


def test_run_jobs_invokes_runner_for_every_job(tmp_path: Path):
    sources = [Path("/input/a.dav"), Path("/input/b.dav"), Path("/input/c.dav")]
    opts = make_options(tmp_path)
    runner = FakeRunner()
    ctrl = ConverterController(runner)
    jobs = ctrl.build_jobs(sources, opts)

    ctrl.run_jobs(jobs, lambda *_: None)

    assert len(runner.calls) == 3


def test_run_jobs_runner_called_in_order(tmp_path: Path):
    sources = [Path("/input/x.dav"), Path("/input/y.dav")]
    opts = make_options(tmp_path)
    runner = FakeRunner()
    ctrl = ConverterController(runner)
    jobs = ctrl.build_jobs(sources, opts)

    ctrl.run_jobs(jobs, lambda *_: None)

    assert runner.calls[0].source == Path("/input/x.dav")
    assert runner.calls[1].source == Path("/input/y.dav")


def test_run_jobs_continues_after_error(tmp_path: Path):
    sources = [Path("/input/a.dav"), Path("/input/b.dav"), Path("/input/c.dav")]
    opts = make_options(tmp_path)
    # Fail on index 1 (second job).
    runner = FakeRunner(fail_on_indices={1})
    ctrl = ConverterController(runner)
    jobs = ctrl.build_jobs(sources, opts)

    failures = ctrl.run_jobs(jobs, lambda *_: None)

    # All three jobs were attempted.
    assert len(runner.calls) == 3
    # Exactly one failure recorded.
    assert len(failures) == 1
    assert failures[0][0].source == Path("/input/b.dav")
    assert isinstance(failures[0][1], FFmpegError)


def test_run_jobs_returns_empty_on_all_success(tmp_path: Path):
    sources = [Path("/input/a.dav"), Path("/input/b.dav")]
    opts = make_options(tmp_path)
    ctrl = ConverterController(FakeRunner())
    jobs = ctrl.build_jobs(sources, opts)

    failures = ctrl.run_jobs(jobs, lambda *_: None)
    assert failures == []


def test_run_jobs_empty_job_list(tmp_path: Path):
    ctrl = ConverterController(FakeRunner())
    failures = ctrl.run_jobs([], lambda *_: None)
    assert failures == []


def test_run_jobs_on_progress_1_indexed(tmp_path: Path):
    sources = [Path("/input/only.dav")]
    opts = make_options(tmp_path)
    ctrl = ConverterController(FakeRunner())
    jobs = ctrl.build_jobs(sources, opts)

    received: list[int] = []
    ctrl.run_jobs(jobs, lambda i, _t, _n: received.append(i))

    assert received[0] == 1


# ---------------------------------------------------------------------------
# cancellation
# ---------------------------------------------------------------------------


def test_run_jobs_stops_when_cancel_event_already_set(tmp_path: Path):
    sources = [Path("/input/a.dav"), Path("/input/b.dav"), Path("/input/c.dav")]
    opts = make_options(tmp_path)
    runner = FakeRunner()
    ctrl = ConverterController(runner)
    jobs = ctrl.build_jobs(sources, opts)

    cancel = threading.Event()
    cancel.set()

    failures = ctrl.run_jobs(jobs, lambda *_: None, cancel_event=cancel)

    assert runner.calls == []
    assert failures == []


def test_run_jobs_stops_mid_batch_when_cancel_set_between_jobs(tmp_path: Path):
    sources = [Path("/input/a.dav"), Path("/input/b.dav"), Path("/input/c.dav")]
    opts = make_options(tmp_path)
    runner = FakeRunner()
    ctrl = ConverterController(runner)
    jobs = ctrl.build_jobs(sources, opts)

    cancel = threading.Event()

    def on_progress(current: int, _total: int, _name: str) -> None:
        if current == 2:
            cancel.set()

    ctrl.run_jobs(jobs, on_progress, cancel_event=cancel)

    # First two jobs ran; third was skipped because cancel was set between jobs.
    assert len(runner.calls) == 2
    assert runner.calls[0].source == Path("/input/a.dav")
    assert runner.calls[1].source == Path("/input/b.dav")


def test_run_jobs_without_cancel_event_runs_all(tmp_path: Path):
    sources = [Path("/input/a.dav"), Path("/input/b.dav")]
    opts = make_options(tmp_path)
    runner = FakeRunner()
    ctrl = ConverterController(runner)
    jobs = ctrl.build_jobs(sources, opts)

    ctrl.run_jobs(jobs, lambda *_: None)
    assert len(runner.calls) == 2
