from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ConversionJob:
    source: Path
    destination: Path
    include_audio: bool
