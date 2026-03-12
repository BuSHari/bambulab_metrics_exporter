from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bambulab_metrics_exporter.security import decrypt_json, encrypt_json, ensure_parent


def save_encrypted_credentials(path: Path, secret: str, payload: dict[str, Any]) -> None:
    ensure_parent(path)
    ciphertext = encrypt_json(secret, json.dumps(payload, ensure_ascii=False))
    path.write_bytes(ciphertext)
    path.chmod(0o600)


def load_encrypted_credentials(path: Path, secret: str) -> dict[str, Any]:
    blob = path.read_bytes()
    plaintext = decrypt_json(secret, blob)
    raw = json.loads(plaintext)
    if not isinstance(raw, dict):
        raise ValueError("Credentials payload must be a JSON object")
    return raw
