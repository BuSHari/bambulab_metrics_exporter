from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from urllib import error, request

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
    print("Use these env vars in .env:")
    print("BAMBULAB_TRANSPORT=cloud_mqtt")
    print(f"BAMBULAB_CLOUD_USER_ID={result.user_id}")
    print(f"BAMBULAB_CLOUD_ACCESS_TOKEN={result.access_token}")
    print("# optional")
    print("# BAMBULAB_CLOUD_MQTT_HOST=us.mqtt.bambulab.com")
    print("# BAMBULAB_CLOUD_MQTT_PORT=8883")
    print("# BAMBULAB_CLOUD_REFRESH_TOKEN=<value>")
    print(f"# token_expires_in_seconds={result.expires_in}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
