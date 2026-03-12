import pytest

from bambulab_metrics_exporter.config import Settings
from bambulab_metrics_exporter.startup import _validate_local


def test_validate_local_missing_vars() -> None:
    settings = Settings(
        bambulab_transport="local_mqtt",
        bambulab_host="",
        bambulab_serial="",
        bambulab_access_code="",
    )
    with pytest.raises(RuntimeError):
        _validate_local(settings)
