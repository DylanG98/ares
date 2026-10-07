#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
python3 scripts/setup.py
git submodule update --init --recursive
docker compose up -d --build --wait
docker compose run --rm operator bootstrap
