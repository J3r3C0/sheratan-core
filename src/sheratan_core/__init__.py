"""Sheratan Core package initialization."""
from .config import get_settings, is_feature_enabled, load_environment

# Ensure the configured profile is loaded as soon as the package is imported.
load_environment()

__all__ = [
    "get_settings",
    "is_feature_enabled",
    "load_environment",
]
