from __future__ import annotations

from bambulab_metrics_exporter.config import Settings
from bambulab_metrics_exporter.startup import startup_validate


def test_startup_validate_cloud_with_valid_probe(monkeypatch) -> None:
    settings = Settings(
        bambulab_transport="cloud_mqtt",
        bambulab_serial="SERIAL",
        bambulab_cloud_user_id="uid",
        bambulab_cloud_access_token="token",
    )
    monkeypatch.setattr("bambulab_metrics_exporter.startup._probe_connection", lambda _s: True)
    startup_validate(settings)


def test_startup_validate_local_calls_probe(monkeypatch) -> None:
    settings = Settings(
        bambulab_transport="local_mqtt",
        bambulab_host="127.0.0.1",
        bambulab_serial="SERIAL",
        bambulab_access_code="ACCESS",
    )
    monkeypatch.setattr("bambulab_metrics_exporter.startup._probe_connection", lambda _s: True)
    startup_validate(settings)
