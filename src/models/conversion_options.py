from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ConversionOptions:
    output_dir: Path
    include_audio: bool
