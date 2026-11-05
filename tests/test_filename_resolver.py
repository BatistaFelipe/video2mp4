from __future__ import annotations

from pathlib import Path

import pytest

from src.models.filename_resolver import resolve_destination


def test_free_on_disk_and_not_reserved(tmp_path: Path):
    source = Path("/input/video.dav")
    result = resolve_destination(source, tmp_path, reserved=set())
    assert result == tmp_path / "video.mp4"


def test_exists_on_disk_returns_suffix_1(tmp_path: Path):
    source = Path("/input/video.dav")
    (tmp_path / "video.mp4").touch()
    result = resolve_destination(source, tmp_path, reserved=set())
    assert result == tmp_path / "video_1.mp4"


def test_reserved_but_not_on_disk_returns_suffix_1(tmp_path: Path):
    source = Path("/input/video.dav")
    reserved = {tmp_path / "video.mp4"}
    result = resolve_destination(source, tmp_path, reserved=reserved)
    assert result == tmp_path / "video_1.mp4"


def test_stem_and_suffix_1_both_exist_returns_suffix_2(tmp_path: Path):
    source = Path("/input/video.dav")
    (tmp_path / "video.mp4").touch()
    (tmp_path / "video_1.mp4").touch()
    result = resolve_destination(source, tmp_path, reserved=set())
    assert result == tmp_path / "video_2.mp4"


def test_source_no_suffix(tmp_path: Path):
    source = Path("/input/videofile")
    result = resolve_destination(source, tmp_path, reserved=set())
    assert result == tmp_path / "videofile.mp4"


def test_source_multi_part_suffix(tmp_path: Path):
    source = Path("/input/cam.rec.dav")
    result = resolve_destination(source, tmp_path, reserved=set())
    assert result == tmp_path / "cam.rec.mp4"


def test_does_not_mutate_reserved(tmp_path: Path):
    source = Path("/input/video.dav")
    reserved: set[Path] = set()
    resolve_destination(source, tmp_path, reserved=reserved)
    assert len(reserved) == 0


def test_collision_via_reserved_and_disk_combined(tmp_path: Path):
    source = Path("/input/clip.dav")
    (tmp_path / "clip.mp4").touch()
    reserved = {tmp_path / "clip_1.mp4"}
    result = resolve_destination(source, tmp_path, reserved=reserved)
    assert result == tmp_path / "clip_2.mp4"
