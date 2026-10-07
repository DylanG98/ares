#!/usr/bin/env sh
set -eu
# Only this isolated project's named-volume roots are initialized as root.
if [ "$(id -u)" = "0" ]; then
  mkdir -p /data/hermes /data/dossiers /data/workspaces /data/state /paperclip
  chown node:node /data /data/hermes /data/dossiers /data/workspaces /data/state /paperclip
  exec gosu node "$@"
fi
exec "$@"
