from bambulab_metrics_exporter.cloud_auth import _as_int, _extract_user_id


def test_as_int_conversions() -> None:
    assert _as_int(5) == 5
    assert _as_int("7") == 7
    assert _as_int(True) == 1
    assert _as_int("bad", default=3) == 3


def test_extract_user_id_from_response() -> None:
    data = {"uid": 1234}
    uid = _extract_user_id(data, "x.y.z", timeout_seconds=1, retries=0, api_bases=[])
    assert uid == "1234"
