$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
python scripts/setup.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git submodule update --init --recursive
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
docker compose up -d --build --wait
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
docker compose run --rm operator bootstrap
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Panel: http://127.0.0.1:3107. Credenciales locales en .env. Seguí README.md para conectar Hermes."
