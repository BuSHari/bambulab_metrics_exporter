from __future__ import annotations

from pathlib import Path

from bambulab_metrics_exporter import main


def test_safe_load_dotenv_missing_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    main._safe_load_dotenv()


def test_bootstrap_cloud_credentials_loads_from_encrypted_store(tmp_path: Path, monkeypatch) -> None:
    creds = tmp_path / "credentials.enc.json"
    creds.write_bytes(b"dummy")

    monkeypatch.setenv("BAMBULAB_TRANSPORT", "cloud_mqtt")
    monkeypatch.setenv("BAMBULAB_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("BAMBULAB_CREDENTIALS_FILE", "credentials.enc.json")
    monkeypatch.setenv("BAMBULAB_SECRET_KEY", "secret")
    monkeypatch.delenv("BAMBULAB_CLOUD_USER_ID", raising=False)
    monkeypatch.delenv("BAMBULAB_CLOUD_ACCESS_TOKEN", raising=False)

    monkeypatch.setattr(
        "bambulab_metrics_exporter.main.load_encrypted_credentials",
        lambda path, secret: {
            "BAMBULAB_CLOUD_USER_ID": "123",
            "BAMBULAB_CLOUD_ACCESS_TOKEN": "token",
        },
    )

    main._bootstrap_cloud_credentials()

    assert "BAMBULAB_CLOUD_USER_ID" in __import__("os").environ
    assert "BAMBULAB_CLOUD_ACCESS_TOKEN" in __import__("os").environ


def test_persist_runtime_env_permission_error(monkeypatch) -> None:
    def fail(_):
        raise PermissionError("denied")

    monkeypatch.setattr("bambulab_metrics_exporter.main.sync_env_file", fail)
    main._persist_runtime_env(Path(".env"))
