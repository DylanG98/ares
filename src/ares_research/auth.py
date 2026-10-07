"""Read supported Hermes auth status without exposing provider credentials."""

import json
import os
import subprocess
from pathlib import Path


def hermes_auth_status(data: Path, role: str = "ceo") -> dict:
    python = Path(os.environ.get("HERMES_PYTHON", "/opt/hermes/.venv/bin/python"))
    if not python.exists():
        return {
            "provider": "openai-codex",
            "logged_in": False,
            "reason": "Hermes runtime not installed here",
        }
    code = (
        "import json; from hermes_cli.auth import get_codex_auth_status; "
        "s=get_codex_auth_status(); "
        "print(json.dumps({'provider':'openai-codex','logged_in':bool(s.get('logged_in'))}))"
    )
    environment = {**os.environ, "HERMES_HOME": str(data / "hermes/profiles" / role)}
    try:
        result = subprocess.run(
            [str(python), "-c", code],
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode:
            return {
                "provider": "openai-codex",
                "logged_in": False,
                "reason": "Hermes status failed; run hermes doctor locally",
            }
        return json.loads(result.stdout.strip().splitlines()[-1])
    except (subprocess.TimeoutExpired, ValueError, IndexError):
        return {
            "provider": "openai-codex",
            "logged_in": False,
            "reason": "Hermes status unavailable",
        }
