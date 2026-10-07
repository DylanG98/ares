"""Create local-only credentials once; never print or replace existing secrets."""

import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[1]
target = root / ".env"
if target.exists():
    print(".env ya existe; se conserva sin cambios.")
else:
    content = (
        "ARES_PORT=3107\nARES_BOARD_EMAIL=operador@ares.local\n"
        f"ARES_BOARD_PASSWORD={secrets.token_urlsafe(32)}\n"
        f"BETTER_AUTH_SECRET={secrets.token_hex(32)}\n"
        f"PAPERCLIP_AGENT_JWT_SECRET={secrets.token_hex(32)}\nARES_MODEL=\n"
    )
    with target.open("x", encoding="utf-8") as stream:
        stream.write(content)
    target.chmod(0o600)
    print(".env creado. Credenciales del panel guardadas localmente; no se imprimen.")
