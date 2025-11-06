"""Runtime configuration loading for Sheratan Core."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

PROFILE_ENV_VAR = "SHERATAN_PROFILE"
DEFAULT_PROFILE = "dev"

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_DIR = BASE_DIR / "ENV"
BASE_ENV = ENV_DIR / ".env"

_loaded_profile: str | None = None


def _parse_env_file(path: Path) -> Dict[str, str]:
    data: Dict[str, str] = {}
    try:
        lines = path.read_text().splitlines()
    except FileNotFoundError:
        return data

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        data[key.strip()] = value.strip()
    return data


def _coerce_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def load_environment(profile: str | None = None, *, override: bool = False) -> str:
    """Load the base and profile specific ``.env`` files into the process."""

    global _loaded_profile

    requested = profile or os.getenv(PROFILE_ENV_VAR) or DEFAULT_PROFILE

    if override:
        _loaded_profile = None

    if _loaded_profile == requested:
        return requested

    for env_path in (BASE_ENV, ENV_DIR / f".env.{requested}"):
        for key, value in _parse_env_file(env_path).items():
            if override or key not in os.environ:
                os.environ[key] = value

    os.environ.setdefault(PROFILE_ENV_VAR, requested)
    _loaded_profile = requested
    return requested


def reset_environment_state() -> None:
    """Testing helper to clear the cached profile state."""

    global _loaded_profile
    _loaded_profile = None


def _collect_feature_flags(env: Dict[str, str]) -> Dict[str, bool]:
    flags: Dict[str, bool] = {}
    raw_list = env.get("SHERATAN_FEATURE_FLAGS", "")
    for item in raw_list.split(","):
        name = item.strip()
        if not name:
            continue
        flags[name.lower()] = True

    prefix = "SHERATAN_FEATURE_"
    for key, value in env.items():
        if not key.startswith(prefix):
            continue
        flag_name = key[len(prefix) :].lower()
        flags[flag_name] = _coerce_bool(value, default=True)
    return flags


@dataclass(frozen=True)
class Settings:
    profile: str
    host: str
    port: int
    router_spec: str
    hmac_secret: str | None
    metrics_enabled: bool
    feature_flags: Dict[str, bool]

    def feature_enabled(self, name: str) -> bool:
        return self.feature_flags.get(name.lower(), False)


def get_settings() -> Settings:
    """Return the current orchestrator settings."""

    load_environment()
    env = dict(os.environ)

    profile = env.get(PROFILE_ENV_VAR, DEFAULT_PROFILE)
    host = env.get("SHERATAN_HOST", "0.0.0.0")
    port = int(env.get("SHERATAN_PORT", "8000"))
    router_spec = env.get("SHERATAN_ROUTER", "").strip()
    hmac_secret = env.get("SHERATAN_HMAC_SECRET", "").strip() or None
    metrics_enabled = _coerce_bool(env.get("SHERATAN_METRICS_ENABLED"), default=True)
    feature_flags = _collect_feature_flags(env)

    return Settings(
        profile=profile,
        host=host,
        port=port,
        router_spec=router_spec,
        hmac_secret=hmac_secret,
        metrics_enabled=metrics_enabled,
        feature_flags=feature_flags,
    )


def is_feature_enabled(name: str) -> bool:
    """Convenience helper to query feature toggles."""

    return get_settings().feature_enabled(name)


__all__ = [
    "Settings",
    "get_settings",
    "is_feature_enabled",
    "load_environment",
    "reset_environment_state",
]
