import json
from pathlib import Path

import httpx
import pytest

from ares_research.organization import OrganizationService
from ares_research.paperclip import PaperclipClient, PaperclipError
from ares_research.storage import WorkspaceConflict


class FakeBoard:
    def __init__(self):
        self.companies = [{"id": "marketing", "name": "Marketing", "description": "Existing team"}]
        self.agents, self.tasks, self.calls = [], [], []
        self.lose_company_response = False

    def handle(self, request):
        path = request.url.path
        payload = json.loads(request.content) if request.content else {}
        self.calls.append((request.method, path, payload))
        if path == "/api/companies":
            if request.method == "GET":
                return httpx.Response(200, json=self.companies)
            company = {"id": "research", **payload}
            self.companies.append(company)
            if self.lose_company_response:
                self.lose_company_response = False
                raise httpx.ReadTimeout("response lost", request=request)
            return httpx.Response(201, json=company)
        if path == "/api/companies/research":
            return httpx.Response(200, json=self.companies[-1])
        if path == "/api/companies/research/agents":
            if request.method == "GET":
                return httpx.Response(200, json=self.agents)
            agent = {"id": "ceo", **payload}
            self.agents.append(agent)
            return httpx.Response(201, json=agent)
        if path == "/api/companies/research/issues":
            if request.method == "GET":
                return httpx.Response(200, json=self.tasks)
            task = {"id": "commissioning", **payload}
            self.tasks.append(task)
            return httpx.Response(201, json=task)
        return httpx.Response(404, json={"error": "unexpected endpoint"})


@pytest.fixture
def board(tmp_path):
    fake = FakeBoard()
    client = PaperclipClient("http://paperclip", transport=httpx.MockTransport(fake.handle))
    org = OrganizationService(client, Path(__file__).resolve().parents[1], tmp_path)
    # Native skill layout tested separately; this suite isolates control-plane behavior.
    org.profiles = lambda: None
    yield fake, org
    client.close()


def test_bootstrap_is_scoped_idempotent_and_creates_no_fake_specialists(board):
    fake, org = board
    first = org.bootstrap()
    second = org.bootstrap()
    assert first == second
    assert len(fake.companies) == 2 and len(fake.agents) == 1 and len(fake.tasks) == 1
    assert not any("/marketing" in path for _, path, _ in fake.calls)
    assert fake.agents[0]["runtimeConfig"]["heartbeat"]["wakeOnDemand"] is False
    assert fake.tasks[0]["status"] == "backlog"


def test_ambiguous_response_reconciles_without_blind_post_retry(board):
    fake, org = board
    fake.lose_company_response = True
    with pytest.raises(PaperclipError, match="inspect state"):
        org.bootstrap()
    org.bootstrap()
    assert len(fake.companies) == 2
    assert sum(method == "POST" and path == "/api/companies" for method, path, _ in fake.calls) == 1


def test_cannot_adopt_unmarked_company(board):
    fake, org = board
    fake.companies.append(
        {"id": "unrelated", "name": org.manifest["name"], "description": "Not ours"}
    )
    with pytest.raises(WorkspaceConflict):
        org.bootstrap()
    assert not any(method != "GET" for method, _, _ in fake.calls)


def test_operator_cannot_impersonate_ceo_hiring(board, tmp_path):
    _, org = board
    with pytest.raises(PermissionError, match="real Hermes CEO"):
        org.hire("review", tmp_path / "pretend.json")


def test_activation_requires_auth_and_uses_saved_agent_for_adapter_test(board, monkeypatch):
    fake, org = board
    state = org.bootstrap()
    monkeypatch.setattr(
        "ares_research.organization.hermes_auth_status", lambda _: {"logged_in": False}
    )
    with pytest.raises(ValueError, match="login not verified"):
        org.activate("verified-test-model")
    assert not any("test-environment" in path for _, path, _ in fake.calls)
    calls = []
    original = org.client.request

    def request(method, path, data=None):
        calls.append((method, path, data))
        if path == "/api/agents/ceo":
            return fake.agents[0]
        if path.endswith("/test-environment"):
            assert data["agentId"] == "ceo"
            assert data["adapterConfig"]["model"] == "verified-test-model"
            return {"status": "warn", "checks": [{"level": "warn", "code": "hermes_no_api_keys"}]}
        if path == "/api/issues/commissioning":
            return fake.tasks[0]
        return original(method, path, data)

    monkeypatch.setattr(
        "ares_research.organization.hermes_auth_status", lambda _: {"logged_in": True}
    )
    org.client.request = request
    result = org.activate("verified-test-model")
    assert result["company_id"] == state["company_id"]
    assert result["inference"] == "pending Paperclip run evidence"
    assert any(method == "PATCH" and data == {"status": "todo"} for method, _, data in calls)
