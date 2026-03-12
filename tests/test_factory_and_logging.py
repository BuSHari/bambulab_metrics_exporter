from bambulab_metrics_exporter.client.factory import build_client
from bambulab_metrics_exporter.client.local_mqtt import LocalMqttBambuClient
from bambulab_metrics_exporter.config import Settings
from bambulab_metrics_exporter.logging_utils import configure_logging


def test_build_client_local() -> None:
    settings = Settings(
        bambulab_transport="local_mqtt",
        bambulab_host="127.0.0.1",
        bambulab_serial="SERIAL",
        bambulab_access_code="ACCESS",
    )
    client = build_client(settings)
    assert isinstance(client, LocalMqttBambuClient)


def test_configure_logging_smoke() -> None:
    configure_logging("INFO")
