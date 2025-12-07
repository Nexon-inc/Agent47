"""Minimal shim for scikit-learn to satisfy imports during startup iterations.
This is NOT a replacement for the real package; install scikit-learn in production.
"""

from . import ensemble

__all__ = ["ensemble"]
