import httpx
import pytest

from ares_research.paperclip import PaperclipClient, PaperclipError


def test_first_operator_uses_official_claim_only_on_fresh_instance(monkeypatch):
    monkeypatch.setenv("ARES_BOARD_EMAIL", "test@example.com")
    monkeypatch.setenv("ARES_BOARD_PASSWORD", "test-password")
    calls = []

    def handle(request):
        calls.append(request.url.path)
        if request.url.path == "/api/health":
            return httpx.Response(200, json={"bootstrapStatus": "bootstrap_pending"})
        if request.url.path == "/api/auth/sign-in/email":
            return httpx.Response(401, json={})
        if request.url.path == "/api/auth/sign-up/email":
            return httpx.Response(200, json={}, headers={"set-cookie": "session=test; Path=/"})
        if request.url.path == "/api/bootstrap/claim":
            assert "session=test" in request.headers["cookie"]
            return httpx.Response(200, json={"claimed": True})
        raise AssertionError(request.url)

    client = PaperclipClient("http://paperclip", transport=httpx.MockTransport(handle))
    try:
        client.board_login()
        assert calls[-1] == "/api/bootstrap/claim"
    finally:
        client.close()


def test_invalid_existing_credentials_never_reset_or_signup(monkeypatch):
    monkeypatch.setenv("ARES_BOARD_EMAIL", "test@example.com")
    monkeypatch.setenv("ARES_BOARD_PASSWORD", "wrong-password")
    calls = []

    def handle(request):
        calls.append(request.url.path)
        if request.url.path == "/api/health":
            return httpx.Response(200, json={"bootstrapStatus": "ready"})
        return httpx.Response(401, json={})

    client = PaperclipClient("http://paperclip", transport=httpx.MockTransport(handle))
    try:
        with pytest.raises(PaperclipError):
            client.board_login()
        assert calls == ["/api/health", "/api/auth/sign-in/email"]
    finally:
        client.close()
