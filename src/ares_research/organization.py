"""Company-scoped provisioning. Only Hermes CEO may execute specialist hires."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from .auth import hermes_auth_status
from .paperclip import PaperclipClient
from .storage import WorkspaceConflict, atomic_json, exclusive_lock


class OrganizationService:
    def __init__(self, client: PaperclipClient, root: Path, data: Path):
        self.client, self.root, self.data = client, root, data
        self.manifest = json.loads((root / "config/organization.json").read_text())
        self.state_path = data / "state/organization.json"

    def state(self) -> dict:
        if not self.state_path.exists():
            raise ValueError("Run bootstrap first")
        state = json.loads(self.state_path.read_text())
        company = self.client.request("GET", f"/api/companies/{state['company_id']}")
        if company.get("description") != self.company_description:
            raise WorkspaceConflict("Company marker mismatch; no mutation permitted")
        return state

    @property
    def company_description(self) -> str:
        return f"{self.manifest['description']} [ares:{self.manifest['key']}]"

    def profiles(self):
        upstream = self.root / "vendor/hermes-agent/skills"
        if not upstream.exists():
            upstream = Path("/opt/hermes/skills")
        native_paths = {
            "grounded-citations": "research/grounded-citations",
            "pdf": "productivity/pdf",
            "xlsx": "productivity/xlsx",
            "docx": "productivity/docx",
            "powerpoint": "productivity/powerpoint",
        }
        for role in self.manifest["roles"]:
            profile = self.data / "hermes/profiles" / role["key"]
            (profile / "skills").mkdir(parents=True, exist_ok=True)
            (self.data / "workspaces" / role["key"]).mkdir(parents=True, exist_ok=True)
            config = profile / "config.yaml"
            if not config.exists():
                config.write_text(
                    "model:\n  provider: openai-codex\nagent:\n  max_turns: 40\nterminal:\n  backend: local\n",
                    encoding="utf-8",
                )
            for name in role["skills"]:
                source = (
                    upstream / native_paths[name]
                    if name in native_paths
                    else self.root / "skills" / name
                )
                target = profile / "skills" / name
                if not (source / "SKILL.md").exists():
                    raise FileNotFoundError(f"Missing skill {name}: {source}")
                # No Windows symlink privilege; copy only into this project's dedicated skill namespace.
                if target.exists():
                    continue  # Updates are explicit, never overwrite agent-owned changes silently.
                shutil.copytree(source, target)

    def payload(self, role: dict, model: str, ceo_id: str | None = None) -> dict:
        return {
            "name": role["name"],
            "role": role["role"],
            "title": role["title"],
            "reportsTo": ceo_id,
            "adapterType": "hermes_local",
            "capabilities": ", ".join(role["skills"]),
            "permissions": {"canCreateAgents": False, "canCreateSkills": False},
            "adapterConfig": {
                "provider": "openai-codex",
                "model": model,
                "hermesCommand": "/usr/local/bin/ares-hermes",
                "cwd": str(self.data / "workspaces" / role["key"]),
                "env": {
                    "HERMES_HOME": str(self.data / "hermes/profiles" / role["key"]),
                    "ARES_ROLE": role["key"],
                    "ARES_DATA": str(self.data),
                },
                "toolsets": "terminal,file,web",
                "maxTurnsPerRun": 40,
                "timeoutSec": 900,
                "graceSec": 15,
                "persistSession": True,
                "checkpoints": True,
            },
            "instructionsBundle": {
                "files": {
                    "AGENTS.md": (self.root / "agents" / f"{role['key']}.md").read_text(),
                    "POLICY.md": (self.root / "agents/POLICY.md").read_text(),
                }
            },
            "runtimeConfig": {
                "heartbeat": {"enabled": False, "wakeOnDemand": False, "maxConcurrentRuns": 1}
            },
            "metadata": {"ares_key": self.manifest["key"], "ares_role": role["key"]},
        }

    def bootstrap(self) -> dict:
        if self.client.agent_mode:
            raise PermissionError("Bootstrap requires the operator")
        with exclusive_lock(self.data / "state/provision.lock"):
            self.profiles()
            companies = self.client.request("GET", "/api/companies")
            matches = [c for c in companies if c.get("description") == self.company_description]
            same_name = [c for c in companies if c["name"] == self.manifest["name"]]
            if len(matches) > 1 or (same_name and not matches):
                raise WorkspaceConflict("Ambiguous existing company; inspect before adopting")
            if matches:
                company = matches[0]
            else:
                company = self.client.request(
                    "POST",
                    "/api/companies",
                    {"name": self.manifest["name"], "description": self.company_description},
                )
            cid = company["id"]
            # Authorized, scoped routine hiring. Does not change other organizations.
            self.client.request(
                "PATCH", f"/api/companies/{cid}", {"requireBoardApprovalForNewAgents": False}
            )
            agents = self.client.request("GET", f"/api/companies/{cid}/agents")
            ceos = [a for a in agents if (a.get("metadata") or {}).get("ares_role") == "ceo"]
            if len(ceos) > 1:
                raise WorkspaceConflict("Duplicate CEO; resolve manually")
            if ceos:
                ceo = ceos[0]
            else:
                payload = self.payload(self.manifest["roles"][0], "CONFIGURE_AFTER_CHATGPT_LOGIN")
                payload["permissions"] = {"canCreateAgents": True, "canCreateSkills": True}
                ceo = self.client.request("POST", f"/api/companies/{cid}/agents", payload)
            marker = "[ares:commissioning:v1]"
            tasks = [
                t for t in self.client.list_issues(cid) if marker in (t.get("description") or "")
            ]
            if len(tasks) > 1:
                raise WorkspaceConflict("Duplicate commissioning task")
            task = (
                tasks[0]
                if tasks
                else self.client.request(
                    "POST",
                    f"/api/companies/{cid}/issues",
                    {
                        "title": "Constituir el equipo independiente de Research y Valuación",
                        "description": marker
                        + "\n"
                        + (self.root / "templates/commissioning.md").read_text(),
                        "assigneeAgentId": ceo["id"],
                        "status": "backlog",
                        "priority": "high",
                    },
                )
            )
            state = {
                "key": self.manifest["key"],
                "company_id": cid,
                "ceo_id": ceo["id"],
                "commissioning_issue_id": task["id"],
            }
            atomic_json(self.state_path, state)
            return {
                **state,
                "status": "awaiting_chatgpt_login",
                "specialists": "CEO hires after authentication; not fabricated",
            }

    def activate(self, model: str) -> dict:
        if self.client.agent_mode:
            raise PermissionError("Provider activation requires the operator")
        if not model.strip() or model.startswith("CONFIGURE"):
            raise ValueError("Provide a model actually available in Hermes after login")
        state = self.state()
        if not hermes_auth_status(self.data).get("logged_in"):
            raise ValueError("ChatGPT login not verified by Hermes; run hermes model first")
        ceo = self.client.request("GET", f"/api/agents/{state['ceo_id']}")
        config = {**ceo["adapterConfig"], "model": model}
        result = self.client.request(
            "POST",
            f"/api/companies/{state['company_id']}/adapters/hermes_local/test-environment",
            {"agentId": ceo["id"], "adapterConfig": config},
        )
        checks = result.get("checks", [])
        blocking = [
            c
            for c in checks
            if c.get("level") == "error"
            or (c.get("level") == "warn" and c.get("code") != "hermes_no_api_keys")
        ]
        if result.get("status") == "fail" or blocking:
            atomic_json(self.data / "state/adapter-check.json", result)
            raise ValueError(
                "Adapter test did not pass; see state/adapter-check.json. No wake issued."
            )
        # Environment test is not an inference proof. CEO's bounded commissioning run supplies that proof.
        self.client.request(
            "PATCH",
            f"/api/agents/{ceo['id']}",
            {
                "adapterConfig": config,
                "runtimeConfig": {
                    "heartbeat": {"enabled": False, "wakeOnDemand": True, "maxConcurrentRuns": 1}
                },
            },
        )
        task = self.client.request("GET", f"/api/issues/{state['commissioning_issue_id']}")
        if task["status"] == "backlog":
            self.client.request("PATCH", f"/api/issues/{task['id']}", {"status": "todo"})
        return {
            "company_id": state["company_id"],
            "model": model,
            "environment": result["status"],
            "inference": "pending Paperclip run evidence",
        }

    def hire(self, role_key: str, decision_path: Path) -> dict:
        if not self.client.agent_mode:
            raise PermissionError(
                "Only the real Hermes CEO may hire; operator cannot impersonate decisions"
            )
        state = self.state()
        me = self.client.request("GET", "/api/agents/me")
        if me["id"] != state["ceo_id"] or me["companyId"] != state["company_id"]:
            raise PermissionError("CEO identity/company mismatch")
        if role_key == "ceo":
            raise ValueError("CEO already exists")
        role = next(r for r in self.manifest["roles"] if r["key"] == role_key)
        decision = json.loads(decision_path.read_text())
        if len(decision.get("candidates", [])) < 3 or not decision.get("rationale"):
            raise ValueError("Hiring requires at least three reviewed candidates and a rationale")
        for candidate in decision["candidates"]:
            if not all(
                candidate.get(k)
                for k in ["url", "commit", "file", "license", "score", "limitations"]
            ):
                raise ValueError("Candidate evidence is incomplete")
        with exclusive_lock(self.data / "state/hiring.lock"):
            agents = self.client.request("GET", f"/api/companies/{state['company_id']}/agents")
            matches = [a for a in agents if (a.get("metadata") or {}).get("ares_role") == role_key]
            if len(matches) > 1:
                raise WorkspaceConflict("Duplicate role")
            if matches:
                self.client.request(
                    "PATCH",
                    f"/api/agents/{matches[0]['id']}/permissions",
                    {"canCreateAgents": False, "canCreateSkills": False, "canAssignTasks": False},
                )
                return {"agent_id": matches[0]["id"], "reused": True}
            decision_record = {**decision, "ceo_id": me["id"], "at": datetime.now(UTC).isoformat()}
            atomic_json(self.data / "state/decisions" / f"{role_key}.json", decision_record)
            payload = self.payload(role, me["adapterConfig"]["model"], me["id"])
            payload["runtimeConfig"]["heartbeat"]["wakeOnDemand"] = True
            payload["sourceIssueId"] = state["commissioning_issue_id"]
            result = self.client.request(
                "POST", f"/api/companies/{state['company_id']}/agent-hires", payload
            )
            self.client.request(
                "PATCH",
                f"/api/agents/{result['agent']['id']}/permissions",
                {"canCreateAgents": False, "canCreateSkills": False, "canAssignTasks": False},
            )
            return result
