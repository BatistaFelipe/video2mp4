from __future__ import annotations

from pathlib import Path


def resolve_destination(source: Path, output_dir: Path, reserved: set[Path]) -> Path:
    stem = source.stem
    candidate = output_dir / f"{stem}.mp4"

    counter = 1
    while candidate.exists() or candidate in reserved:
        candidate = output_dir / f"{stem}_{counter}.mp4"
        counter += 1

    return candidate
