from __future__ import annotations

import pytest
from pathlib import Path

from src.models.conversion_job import ConversionJob


def test_equality():
    a = ConversionJob(
        source=Path("/input/video.dav"),
        destination=Path("/out/video.mp4"),
        include_audio=True,
    )
    b = ConversionJob(
        source=Path("/input/video.dav"),
        destination=Path("/out/video.mp4"),
        include_audio=True,
    )
    assert a == b


def test_inequality_different_source():
    a = ConversionJob(Path("/a.dav"), Path("/out.mp4"), True)
    b = ConversionJob(Path("/b.dav"), Path("/out.mp4"), True)
    assert a != b


def test_inequality_different_destination():
    a = ConversionJob(Path("/a.dav"), Path("/out1.mp4"), True)
    b = ConversionJob(Path("/a.dav"), Path("/out2.mp4"), True)
    assert a != b


def test_inequality_different_audio():
    a = ConversionJob(Path("/a.dav"), Path("/out.mp4"), True)
    b = ConversionJob(Path("/a.dav"), Path("/out.mp4"), False)
    assert a != b


def test_immutability_source():
    job = ConversionJob(Path("/a.dav"), Path("/out.mp4"), True)
    with pytest.raises((AttributeError, TypeError)):
        job.source = Path("/other.dav")  # type: ignore[misc]


def test_immutability_destination():
    job = ConversionJob(Path("/a.dav"), Path("/out.mp4"), True)
    with pytest.raises((AttributeError, TypeError)):
        job.destination = Path("/other.mp4")  # type: ignore[misc]


def test_immutability_include_audio():
    job = ConversionJob(Path("/a.dav"), Path("/out.mp4"), False)
    with pytest.raises((AttributeError, TypeError)):
        job.include_audio = True  # type: ignore[misc]


def test_fields_stored_correctly():
    src = Path("/input/cam.dav")
    dst = Path("/output/cam.mp4")
    job = ConversionJob(source=src, destination=dst, include_audio=False)
    assert job.source == src
    assert job.destination == dst
    assert job.include_audio is False
