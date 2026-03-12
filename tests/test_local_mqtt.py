from __future__ import annotations

import json
from types import SimpleNamespace

from bambulab_metrics_exporter.client.local_mqtt import LocalMqttBambuClient, _deep_merge_in_place
from bambulab_metrics_exporter.config import Settings


class _SubClient:
    def __init__(self) -> None:
        self.subscribed: list[tuple[str, int]] = []

    def subscribe(self, topic: str, qos: int = 0) -> None:
        self.subscribed.append((topic, qos))


def _settings() -> Settings:
    return Settings(
        bambulab_transport="local_mqtt",
        bambulab_host="127.0.0.1",
        bambulab_serial="SERIAL1",
        bambulab_access_code="abc",
    )


def test_deep_merge_in_place() -> None:
    target = {"print": {"a": 1, "b": {"x": 1}}}
    source = {"print": {"b": {"y": 2}, "c": 3}}
    _deep_merge_in_place(target, source)
    assert target["print"]["a"] == 1
    assert target["print"]["b"]["x"] == 1
    assert target["print"]["b"]["y"] == 2
    assert target["print"]["c"] == 3


def test_on_connect_success_subscribes() -> None:
    client = LocalMqttBambuClient(_settings())
    fake = _SubClient()

    client._on_connect(fake, None, None, 0, None)

    assert client._connected is True
    assert fake.subscribed[0][0] == "device/SERIAL1/report"


def test_on_message_updates_state() -> None:
    client = LocalMqttBambuClient(_settings())
    payload = {"print": {"mc_percent": 55}}
    msg = SimpleNamespace(topic="device/SERIAL1/report", payload=json.dumps(payload).encode("utf-8"))

    client._on_message(None, None, msg)

    assert client._latest_state["print"]["mc_percent"] == 55
