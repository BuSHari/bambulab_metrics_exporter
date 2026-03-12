from __future__ import annotations

import base64
import json

import pytest

from bambulab_metrics_exporter.cloud_auth import (
    CloudAuthError,
    _extract_user_id,
    login_with_code,
    send_code,
)


def _jwt_with_uid(uid: str) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none"}).encode()).decode().rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps({"uid": uid}).encode()).decode().rstrip("=")
    return f"{header}.{payload}.sig"


def test_extract_user_id_from_jwt_claims(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "bambulab_metrics_exporter.cloud_auth._resolve_user_id_from_profile",
        lambda **_: None,
    )
    uid = _extract_user_id({}, _jwt_with_uid("777"), timeout_seconds=1, retries=0, api_bases=[])
    assert uid == "777"


def test_extract_user_id_from_profile_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "bambulab_metrics_exporter.cloud_auth._resolve_user_id_from_profile",
        lambda **_: "555",
    )
    uid = _extract_user_id({}, "x.y.z", timeout_seconds=1, retries=0, api_bases=["https://x"])
    assert uid == "555"


def test_login_with_code_parses_result(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "bambulab_metrics_exporter.cloud_auth._post_json_multi_base",
        lambda *args, **kwargs: {
            "accessToken": "token123",
            "refreshToken": "refresh123",
            "expiresIn": "3600",
            "uid": 42,
        },
    )
    result = login_with_code("user@example.com", "123456", timeout_seconds=1, retries=0)
    assert result.user_id == "42"
    assert result.access_token == "token123"


def test_login_with_code_raises_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "bambulab_metrics_exporter.cloud_auth._post_json_multi_base",
        lambda *args, **kwargs: {"error": "bad code"},
    )
    with pytest.raises(CloudAuthError):
        login_with_code("user@example.com", "bad", timeout_seconds=1, retries=0)


def test_send_code_calls_multi_base(monkeypatch: pytest.MonkeyPatch) -> None:
    called = {"ok": False}

    def fake_post(*args, **kwargs):
        called["ok"] = True
        return {}

    monkeypatch.setattr("bambulab_metrics_exporter.cloud_auth._post_json_multi_base", fake_post)
    send_code("user@example.com", timeout_seconds=1, retries=0)
    assert called["ok"] is True
