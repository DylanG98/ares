import json
from datetime import date
from pathlib import Path

import httpx
import pytest

from ares_research.domain import CompanyIdentity
from ares_research.organization import OrganizationService
from ares_research.paperclip import PaperclipClient, PaperclipError
from ares_research.storage import Dossier, atomic_json
from ares_research.workflow import AnalysisWorkflow


def test_dag_recovers_lost_response_and_preserves_independent_dependencies(tmp_path):
    identity = CompanyIdentity(
        legal_name="Synthetic Workflow SA",
        ticker="TEST",
        exchange="TEST",
        instrument="ordinary_share",
        currency="USD",
        cutoff_date=date(2025, 3, 1),
        accounting_standard="synthetic",
        sector="industrial",
        synthetic=True,
    )
    Dossier(tmp_path / "dossiers", identity)
    tasks = []
    lost_response = True
    company_description = None

    def handle(request):
        nonlocal lost_response
        path = request.url.path
        payload = json.loads(request.content) if request.content else {}
        if path == "/api/companies/company":
            return httpx.Response(200, json={"id": "company", "description": company_description})
        if path == "/api/agents/me":
            return httpx.Response(200, json={"id": "ceo", "companyId": "company"})
        if path == "/api/issues/parent":
            return httpx.Response(
                200,
                json={
                    "id": "parent",
                    "companyId": "company",
                    "description": f"[ares:case:{identity.case_id}:request]",
                },
            )
        if path == "/api/companies/company/agents":
            return httpx.Response(
                200,
                json=[
                    {"id": role, "metadata": {"ares_role": role}, "status": "idle"}
                    for role, _, _ in AnalysisWorkflow.STAGES
                ],
            )
        if path == "/api/companies/company/issues":
            if request.method == "GET":
                return httpx.Response(200, json=tasks)
            task = {"id": f"task-{len(tasks)}", **payload}
            tasks.append(task)
            if len(tasks) == 3 and lost_response:
                lost_response = False
                raise httpx.ReadTimeout("response lost after write", request=request)
            return httpx.Response(201, json=task)
        raise AssertionError(path)

    client = PaperclipClient(
        "http://test", token="unit-test-token", transport=httpx.MockTransport(handle)
    )
    org = OrganizationService(client, Path(__file__).resolve().parents[1], tmp_path)
    company_description = org.company_description
    atomic_json(
        org.state_path, {"company_id": "company", "ceo_id": "ceo", "commissioning_issue_id": "init"}
    )
    workflow = AnalysisWorkflow(org)
    try:
        with pytest.raises(PaperclipError):
            workflow.plan(identity.case_id, "parent")
        first = workflow.plan(identity.case_id, "parent")
        assert workflow.plan(identity.case_id, "parent") == first
        assert len(tasks) == 6
        model = next(t for t in tasks if t["assigneeAgentId"] == "valuation")
        reviewer = next(t for t in tasks if t["assigneeAgentId"] == "review")
        assert model["blockedByIssueIds"] == [first["accounting"], first["business"]]
        assert reviewer["blockedByIssueIds"] == [model["id"]]
        assert model["assigneeAgentId"] != reviewer["assigneeAgentId"]
        assert all(t["status"] == "blocked" for t in tasks[1:])
    finally:
        client.close()
