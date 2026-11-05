from __future__ import annotations

import pytest
from pathlib import Path

from src.models.conversion_options import ConversionOptions


def test_equality():
    a = ConversionOptions(output_dir=Path("/out"), include_audio=True)
    b = ConversionOptions(output_dir=Path("/out"), include_audio=True)
    assert a == b


def test_inequality_different_dir():
    a = ConversionOptions(output_dir=Path("/out1"), include_audio=True)
    b = ConversionOptions(output_dir=Path("/out2"), include_audio=True)
    assert a != b


def test_inequality_different_audio():
    a = ConversionOptions(output_dir=Path("/out"), include_audio=True)
    b = ConversionOptions(output_dir=Path("/out"), include_audio=False)
    assert a != b


def test_immutability_output_dir():
    opts = ConversionOptions(output_dir=Path("/out"), include_audio=True)
    with pytest.raises((AttributeError, TypeError)):
        opts.output_dir = Path("/other")  # type: ignore[misc]


def test_immutability_include_audio():
    opts = ConversionOptions(output_dir=Path("/out"), include_audio=False)
    with pytest.raises((AttributeError, TypeError)):
        opts.include_audio = True  # type: ignore[misc]


def test_fields_stored_correctly():
    p = Path("/videos/out")
    opts = ConversionOptions(output_dir=p, include_audio=False)
    assert opts.output_dir == p
    assert opts.include_audio is False
