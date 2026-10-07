#!/usr/bin/env sh
set -eu
case "${1:-}" in
  --version|--help) exec /opt/hermes/.venv/bin/hermes "$@" ;;
esac
case "${HERMES_HOME:-}" in
  /data/hermes/profiles/*) ;;
  *) echo "ARES: a dedicated Hermes profile is required" >&2; exit 78 ;;
esac
# Operator-only credentials and server signing secrets are not agent inputs.
unset ARES_BOARD_PASSWORD ARES_BOARD_EMAIL BETTER_AUTH_SECRET PAPERCLIP_AGENT_JWT_SECRET
exec /opt/hermes/.venv/bin/hermes "$@"
