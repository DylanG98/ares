"""Create a dependency DAG in Paperclip; no external scheduler."""

from __future__ import annotations

from .domain import CompanyIdentity
from .organization import OrganizationService
from .storage import Dossier, WorkspaceConflict, exclusive_lock


class AnalysisWorkflow:
    STAGES = [
        ("research", (), "Identidad, originales y registro de fuentes"),
        ("accounting", ("research",), "Cinco ejercicios, intermedios y normalización contable"),
        ("business", ("research",), "Negocio y perspectivas vinculadas a supuestos"),
        ("valuation", ("accounting", "business"), "Modelo editable, escenarios y sensibilidades"),
        ("review", ("valuation",), "Revisión independiente y hallazgos materiales"),
        ("ceo", ("review",), "Informe final, limitaciones y plan de actualización"),
    ]

    def __init__(self, organization: OrganizationService):
        self.org, self.client = organization, organization.client

    def request(self, identity: CompanyIdentity) -> dict:
        state = self.org.state()
        commissioning = self.client.request("GET", f"/api/issues/{state['commissioning_issue_id']}")
        if commissioning["status"] != "done":
            raise ValueError("CEO must complete real commissioning before company analysis")
        dossier = Dossier(self.org.data / "dossiers", identity)
        marker = f"[ares:case:{identity.case_id}:request]"
        with exclusive_lock(dossier.path / ".request.lock"):
            matches = [
                t
                for t in self.client.list_issues(state["company_id"])
                if marker in (t.get("description") or "")
            ]
            if len(matches) > 1:
                raise WorkspaceConflict("Duplicate requests")
            if matches:
                return matches[0]
            return self.client.request(
                "POST",
                f"/api/companies/{state['company_id']}/issues",
                {
                    "title": f"Analizar {identity.legal_name} ({identity.ticker}, {identity.exchange}) al {identity.cutoff_date}",
                    "description": f"{marker}\nExpediente: {dossier.path}\nIdentidad: {identity.model_dump_json()}\nCEO: crear plan con ares plan --case {identity.case_id} --parent <este issue>. Entrega tras revisión independiente.",
                    "status": "todo",
                    "assigneeAgentId": state["ceo_id"],
                    "priority": "medium",
                },
            )

    def plan(self, case_id: str, parent_id: str) -> dict:
        state = self.org.state()
        if (
            not self.client.agent_mode
            or self.client.request("GET", "/api/agents/me")["id"] != state["ceo_id"]
        ):
            raise PermissionError("Only Hermes CEO creates the DAG")
        if len(case_id) != 24 or any(c not in "0123456789abcdef" for c in case_id):
            raise ValueError("Invalid case ID")
        dossier = self.org.data / "dossiers" / case_id
        identity = CompanyIdentity.model_validate_json((dossier / "identity.json").read_text())
        parent = self.client.request("GET", f"/api/issues/{parent_id}")
        if (
            identity.case_id != case_id
            or parent["companyId"] != state["company_id"]
            or f"[ares:case:{case_id}:request]" not in (parent.get("description") or "")
        ):
            raise PermissionError("Case/parent/company mismatch")
        agents = self.client.request("GET", f"/api/companies/{state['company_id']}/agents")
        roster = {}
        for role, _, _ in self.STAGES:
            matches = [
                a
                for a in agents
                if (a.get("metadata") or {}).get("ares_role") == role
                and a["status"] not in {"terminated", "pending_approval", "paused"}
            ]
            if len(matches) != 1:
                raise ValueError(f"Role {role}: exactly one available agent required")
            roster[role] = matches[0]["id"]
        if roster["review"] == roster["valuation"]:
            raise PermissionError("Independent reviewer required")
        with exclusive_lock(dossier / ".plan.lock"):
            existing = self.client.list_issues(state["company_id"])
            tasks = {}
            for role, dependencies, goal in self.STAGES:
                marker = f"[ares:case:{case_id}:{role}]"
                matches = [t for t in existing if marker in (t.get("description") or "")]
                if len(matches) > 1:
                    raise WorkspaceConflict(f"Duplicate stage {role}")
                task = (
                    matches[0]
                    if matches
                    else self.client.request(
                        "POST",
                        f"/api/companies/{state['company_id']}/issues",
                        {
                            "title": f"{identity.ticker}: {goal}",
                            "parentId": parent_id,
                            "description": f"{marker}\nExpediente {dossier}\nObjetivo: {goal}.\nLeer identidad y entradas pertinentes. Aplicar POLICY.md y skill del rol. Entregar versión/hash, fuentes, controles, dudas y próximo responsable. No ejecutar con dependencias pendientes. Hallazgos materiales bloquean cierre; el autor corrige.",
                            "assigneeAgentId": roster[role],
                            "status": "blocked" if dependencies else "todo",
                            "blockedByIssueIds": [tasks[d]["id"] for d in dependencies],
                            **(
                                {
                                    "unblockDescriptor": {
                                        "owner": {"agentId": state["ceo_id"]},
                                        "action": "Verificar entregables de dependencias y habilitar al completar",
                                    }
                                }
                                if dependencies
                                else {}
                            ),
                        },
                    )
                )
                tasks[role] = task
            return {role: task["id"] for role, task in tasks.items()}
