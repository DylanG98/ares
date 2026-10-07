"""Small API client: no background worker, timer, mutation retry, or second scheduler."""

from __future__ import annotations

import os
from typing import Any

import httpx


class PaperclipError(RuntimeError):
    pass


class PaperclipClient:
    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        run_id: str | None = None,
        origin: str | None = None,
        transport: httpx.BaseTransport | None = None,
    ):
        base_url = base_url.rstrip("/").removesuffix("/api")
        headers = {"Origin": origin or base_url}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if run_id:
            headers["X-Paperclip-Run-Id"] = run_id
        # Internal Docker/localhost traffic must not go to an HTTP proxy.
        self.http = httpx.Client(
            base_url=base_url, headers=headers, timeout=30, transport=transport, trust_env=False
        )
        self.agent_mode = token is not None

    @classmethod
    def from_env(cls):
        token = os.environ.get("PAPERCLIP_API_KEY")
        base = (
            os.environ.get("PAPERCLIP_API_URL") if token else os.environ.get("ARES_PAPERCLIP_URL")
        )
        return cls(
            base or "http://127.0.0.1:3107",
            token,
            os.environ.get("PAPERCLIP_RUN_ID"),
            os.environ.get("ARES_PUBLIC_URL"),
        )

    def close(self):
        self.http.close()

    def request(self, method: str, path: str, data: dict | None = None) -> Any:
        try:
            response = self.http.request(method, path, json=data)
        except httpx.TransportError as exc:
            raise PaperclipError(
                f"{method} {path}: transport failure; inspect state before retrying a mutation"
            ) from exc
        if response.is_error:
            # Response bodies can contain configuration; keep them out of ordinary logs.
            raise PaperclipError(
                f"{method} {path}: HTTP {response.status_code}; inspect Paperclip logs"
            )
        return response.json() if response.content else None

    def board_login(self):
        if self.agent_mode:
            raise PermissionError("An agent must never use board credentials")
        email, password = os.environ.get("ARES_BOARD_EMAIL"), os.environ.get("ARES_BOARD_PASSWORD")
        if not email or not password:
            raise PaperclipError(
                "Operator credentials missing; use docker compose run --rm operator"
            )
        health = self.request("GET", "/api/health")
        # Sign-up is attempted only during a positively identified fresh-instance bootstrap.
        path = "/api/auth/sign-in/email"
        response = self.http.post(path, json={"email": email, "password": password})
        if response.status_code == 401 and health.get("bootstrapStatus") == "bootstrap_pending":
            response = self.http.post(
                "/api/auth/sign-up/email",
                json={"email": email, "password": password, "name": "Operador Ares"},
            )
        if response.is_error:
            raise PaperclipError(
                f"Board login HTTP {response.status_code}; bootstrapStatus={health.get('bootstrapStatus')}. No credential reset attempted."
            )
        if not self.http.cookies:
            raise PaperclipError("Board authentication did not establish a session")

        if health.get("bootstrapStatus") == "bootstrap_pending":
            # Official first-admin endpoint, guarded by the server.
            self.request("POST", "/api/bootstrap/claim", {})

    def list_issues(self, company_id: str) -> list[dict]:
        # Current list endpoint has a bounded default; paginate to find existing markers reliably.
        issues, offset = [], 0
        while True:
            batch = self.request(
                "GET", f"/api/companies/{company_id}/issues?limit=100&offset={offset}"
            )
            if isinstance(batch, dict):
                batch = batch.get("issues", batch.get("data", []))
            issues.extend(batch)
            if len(batch) < 100:
                return issues
            offset += 100
            if offset >= 10000:
                raise PaperclipError("Issue discovery exceeds safe pagination bound")
