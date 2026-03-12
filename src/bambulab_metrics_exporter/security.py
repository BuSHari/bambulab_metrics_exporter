from __future__ import annotations

import base64
import hashlib
from pathlib import Path

from cryptography.fernet import Fernet


def derive_fernet_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_json(secret: str, data: str) -> bytes:
    fernet = Fernet(derive_fernet_key(secret))
    return fernet.encrypt(data.encode("utf-8"))


def decrypt_json(secret: str, blob: bytes) -> str:
    fernet = Fernet(derive_fernet_key(secret))
    return fernet.decrypt(blob).decode("utf-8")


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.parent.chmod(0o700)
    except OSError:
        pass
