from pathlib import Path

import pytest

from bambulab_metrics_exporter.config import Settings
from bambulab_metrics_exporter.startup import _try_cloud_reauth


class _LoginResult:
    def __init__(self) -> None:
        self.user_id = "123"
        self.access_token = "token"
        self.refresh_token = "refresh"


def test_try_cloud_reauth_requires_email(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BAMBULAB_CLOUD_EMAIL", raising=False)
    settings = Settings(bambulab_transport="cloud_mqtt", bambulab_serial="S1")

    with pytest.raises(RuntimeError):
        _try_cloud_reauth(settings)


def test_try_cloud_reauth_saves_credentials(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BAMBULAB_CLOUD_EMAIL", "user@example.com")
    monkeypatch.setenv("BAMBULAB_CLOUD_CODE", "123456")
    monkeypatch.setenv("BAMBULAB_SECRET_KEY", "super-secret")

    called = {"saved": False, "synced": False}

    def fake_login_with_code(email: str, code: str):
        assert email == "user@example.com"
        assert code == "123456"
        return _LoginResult()

    def fake_save_encrypted_credentials(path: Path, secret: str, payload: dict):
        called["saved"] = True
        assert secret == "super-secret"
        assert path.name == "credentials.enc.json"
        assert payload["BAMBULAB_CLOUD_USER_ID"] == "123"

    def fake_sync_env_file(path: Path):
        called["synced"] = True
        assert path.name == ".env"

    monkeypatch.setattr("bambulab_metrics_exporter.startup.login_with_code", fake_login_with_code)
    monkeypatch.setattr(
        "bambulab_metrics_exporter.startup.save_encrypted_credentials",
        fake_save_encrypted_credentials,
    )
    monkeypatch.setattr("bambulab_metrics_exporter.startup.sync_env_file", fake_sync_env_file)

    settings = Settings(
        bambulab_transport="cloud_mqtt",
        bambulab_serial="SERIAL1",
        bambulab_config_dir=str(tmp_path),
        bambulab_credentials_file="credentials.enc.json",
        bambulab_cloud_mqtt_host="us.mqtt.bambulab.com",
        bambulab_cloud_mqtt_port=8883,
    )

    _try_cloud_reauth(settings)

    assert called["saved"] is True
    assert called["synced"] is True
