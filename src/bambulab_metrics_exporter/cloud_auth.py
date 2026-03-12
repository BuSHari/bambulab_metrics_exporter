from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib import error, request

from bambulab_metrics_exporter.credentials_store import save_encrypted_credentials
from bambulab_metrics_exporter.env_sync import sync_env_file

API_BASE = "https://api.bambulab.com"


@dataclass(slots=True)
class LoginResult:
    access_token: str
    refresh_token: str
    expires_in: int
    user_id: str


def _post_json(path: str, payload: dict[str, object]) -> dict[str, object]:
    req = request.Request(
        f"{API_BASE}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=20) as res:
            body = res.read().decode("utf-8")
            return json.loads(body) if body else {}
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc


def send_code(email: str) -> None:
    _post_json("/v1/user-service/user/sendemail/code", {"email": email, "type": "codeLogin"})


def login_with_code(email: str, code: str) -> LoginResult:
    data = _post_json("/v1/user-service/user/login", {"account": email, "code": code})
    if "error" in data:
        raise RuntimeError(str(data["error"]))

    try:
        return LoginResult(
            access_token=str(data["accessToken"]),
            refresh_token=str(data.get("refreshToken", "")),
            expires_in=int(data.get("expiresIn", 0)),
            user_id=str(data["uid"]),
        )
    except KeyError as exc:
        raise RuntimeError(f"Missing expected response key: {exc}") from exc


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bambu Cloud auth helper")
    parser.add_argument("--email", required=True, help="Bambu account email")
    parser.add_argument("--code", help="2FA code from email")
    parser.add_argument("--send-code", action="store_true", help="Send email verification code")
    parser.add_argument("--save", action="store_true", help="Save encrypted credentials in config dir")
    parser.add_argument("--config-dir", default=os.getenv("BAMBULAB_CONFIG_DIR", "/config/bambulab-metrics-exporter"))
    parser.add_argument("--credentials-file", default=os.getenv("BAMBULAB_CREDENTIALS_FILE", "credentials.enc.json"))
    parser.add_argument("--secret-key", default=os.getenv("BAMBULAB_SECRET_KEY", ""))
    parser.add_argument("--serial", default=os.getenv("BAMBULAB_SERIAL", ""))
    parser.add_argument("--env-file", default=".env", help=".env file to update")
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    if args.send_code:
        send_code(args.email)
        print("Verification code sent.")
        return 0

    if not args.code:
        print("--code is required unless --send-code is used", file=sys.stderr)
        return 2

    result = login_with_code(args.email, args.code)

    os.environ["BAMBULAB_TRANSPORT"] = "cloud_mqtt"
    if args.serial:
        os.environ["BAMBULAB_SERIAL"] = args.serial
    os.environ["BAMBULAB_CLOUD_USER_ID"] = result.user_id
    os.environ["BAMBULAB_CLOUD_ACCESS_TOKEN"] = result.access_token
    os.environ["BAMBULAB_CLOUD_REFRESH_TOKEN"] = result.refresh_token
    os.environ.setdefault("BAMBULAB_CLOUD_MQTT_HOST", "us.mqtt.bambulab.com")
    os.environ.setdefault("BAMBULAB_CLOUD_MQTT_PORT", "8883")
    os.environ["BAMBULAB_CONFIG_DIR"] = args.config_dir
    os.environ["BAMBULAB_CREDENTIALS_FILE"] = args.credentials_file
    if args.secret_key:
        os.environ["BAMBULAB_SECRET_KEY"] = args.secret_key

    if args.save:
        if not args.secret_key:
            print("--secret-key (or BAMBULAB_SECRET_KEY) is required with --save", file=sys.stderr)
            return 2
        payload = {
            "BAMBULAB_CLOUD_USER_ID": result.user_id,
            "BAMBULAB_CLOUD_ACCESS_TOKEN": result.access_token,
            "BAMBULAB_CLOUD_REFRESH_TOKEN": result.refresh_token,
            "BAMBULAB_CLOUD_MQTT_HOST": os.environ["BAMBULAB_CLOUD_MQTT_HOST"],
            "BAMBULAB_CLOUD_MQTT_PORT": os.environ["BAMBULAB_CLOUD_MQTT_PORT"],
        }
        save_encrypted_credentials(Path(args.config_dir) / args.credentials_file, args.secret_key, payload)

    sync_env_file(Path(args.env_file))

    print(f"Updated {args.env_file}")
    print("Cloud credentials ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
