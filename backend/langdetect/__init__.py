"""Minimal shim for `langdetect` used by Clara's multilingual service.

This lightweight implementation avoids adding an external dependency during
startup. It returns 'en' for all inputs and exposes a DetectorFactory with a
`seed` attribute to match the real package's surface used by the project.
"""
from typing import Any


def detect(text: str) -> str:
    """Naive fallback: always return English.

    The real `langdetect.detect` returns language codes; for startup and
    non-production environments this fallback prevents import-time failures.
    """
    return "en"


class DetectorFactory:
    """Compatibility object exposing a `seed` attribute used by callers."""
    seed: Any = None


__all__ = ["detect", "DetectorFactory"]
