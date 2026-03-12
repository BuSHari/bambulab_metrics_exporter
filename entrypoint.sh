#!/usr/bin/env sh
set -eu

PUID="${PUID:-99}"
PGID="${PGID:-100}"
UMASK="${UMASK:-002}"

# Ensure container user/group match host permissions (Unraid style).
if getent group appgroup >/dev/null 2>&1; then
  groupmod -o -g "$PGID" appgroup 2>/dev/null || true
else
  groupadd -o -g "$PGID" appgroup || true
fi

if id appuser >/dev/null 2>&1; then
  usermod -o -u "$PUID" -g "$PGID" appuser 2>/dev/null || true
else
  useradd -o -u "$PUID" -g "$PGID" -m -s /usr/sbin/nologin appuser || true
fi

umask "$UMASK"

mkdir -p /config/bambulab-metrics-exporter /app
chown -R "$PUID:$PGID" /config/bambulab-metrics-exporter || true
chown -R "$PUID:$PGID" /app || true

exec gosu "$PUID:$PGID" "$@"
