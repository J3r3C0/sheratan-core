import os
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from sheratan_core import config


@pytest.fixture(autouse=True)
def reset_profile_state(monkeypatch):
    # Ensure tests do not leak process-wide state.
    config.reset_environment_state()
    for key in list(os.environ):
        if key.startswith("SHERATAN_"):
            monkeypatch.delenv(key, raising=False)
    yield
    config.reset_environment_state()


def test_profile_environment_loading(monkeypatch, tmp_path):
    env_dir = tmp_path / "ENV"
    env_dir.mkdir()
    base_env = env_dir / ".env"
    base_env.write_text(
        "\n".join(
            [
                "SHERATAN_PORT=8100",
                "SHERATAN_METRICS_ENABLED=1",
                "SHERATAN_FEATURE_FLAGS=metrics,alpha",
            ]
        )
    )
    staging_env = env_dir / ".env.staging"
    staging_env.write_text(
        "\n".join(
            [
                "SHERATAN_PORT=9100",
                "SHERATAN_ROUTER=test.router:create",
                "SHERATAN_HMAC_SECRET=stage-secret",
                "SHERATAN_FEATURE_ALPHA=0",
                "SHERATAN_FEATURE_BETA=1",
            ]
        )
    )

    monkeypatch.setenv(config.PROFILE_ENV_VAR, "staging")
    monkeypatch.setattr(config, "ENV_DIR", env_dir, raising=False)
    monkeypatch.setattr(config, "BASE_ENV", base_env, raising=False)

    loaded = config.load_environment(override=True)
    assert loaded == "staging"
    assert os.environ[config.PROFILE_ENV_VAR] == "staging"

    settings = config.get_settings()
    assert settings.profile == "staging"
    assert settings.port == 9100
    assert settings.router_spec == "test.router:create"
    # HMAC secret is optional but should be populated when provided
    assert settings.hmac_secret == "stage-secret"
    assert settings.metrics_enabled is True
    assert settings.feature_enabled("metrics") is True
    # The explicit zero flag should override the list default
    assert settings.feature_enabled("alpha") is False
    assert settings.feature_enabled("beta") is True


def test_existing_env_values_are_preserved(monkeypatch, tmp_path):
    env_dir = tmp_path / "ENV"
    env_dir.mkdir()
    (env_dir / ".env").write_text("SHERATAN_PORT=8200\n")
    (env_dir / ".env.dev").write_text("SHERATAN_PORT=8300\n")

    monkeypatch.setenv("SHERATAN_PORT", "9999")
    monkeypatch.setattr(config, "ENV_DIR", env_dir, raising=False)
    monkeypatch.setattr(config, "BASE_ENV", env_dir / ".env", raising=False)

    config.load_environment(profile="dev")
    settings = config.get_settings()

    # Since the variable was already set the loader should not override it.
    assert settings.port == 9999
