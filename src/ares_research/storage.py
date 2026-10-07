"""Content-addressed originals, exclusive writes and append-only revisions."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from .domain import CompanyIdentity, FinancialFact, Source


class WorkspaceConflict(RuntimeError):
    pass


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, default=str, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


@contextmanager
def exclusive_lock(path: Path):
    """Fail closed after an interrupted writer; never steal a live/stale lock automatically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise WorkspaceConflict(
            f"Lock exists: {path}. Inspect interrupted work before recovery."
        ) from exc
    try:
        os.write(descriptor, str(os.getpid()).encode())
        os.close(descriptor)
        yield
    finally:
        path.unlink(missing_ok=True)


class Dossier:
    OWNERS = {
        "extracted": "research",
        "normalized": "accounting",
        "adjustments": "accounting",
        "business": "business",
        "assumptions": "valuation",
        "model": "valuation",
        "reviews": "review",
        "report": "ceo",
        "handoffs": None,
    }

    def __init__(self, root: Path, identity: CompanyIdentity):
        self.identity = identity
        self.path = root / identity.case_id
        self.path.mkdir(parents=True, exist_ok=True)
        with exclusive_lock(self.path / ".init.lock"):
            target = self.path / "identity.json"
            if target.exists():
                if CompanyIdentity.model_validate_json(target.read_text()) != identity:
                    raise WorkspaceConflict("Dossier identity mismatch")
            else:
                atomic_json(target, identity.model_dump(mode="json"))
            for folder in ["originals", "sources", *self.OWNERS]:
                (self.path / folder).mkdir(exist_ok=True)

    def add_source(self, source: Source, content: bytes) -> Path:
        if source.published_on > self.identity.cutoff_date:
            raise ValueError("Look-ahead: source was not public at the cutoff")
        if source.retrieved_on < source.published_on:
            raise ValueError("Retrieval predates publication")
        if (source.kind == "synthetic") != self.identity.synthetic:
            raise ValueError("Never mix synthetic and real evidence")
        if hashlib.sha256(content).hexdigest() != source.sha256:
            raise ValueError("Source checksum mismatch")
        with exclusive_lock(self.path / ".sources.lock"):
            original = self.path / "originals" / source.sha256
            if (
                original.exists()
                and hashlib.sha256(original.read_bytes()).hexdigest() != source.sha256
            ):
                raise WorkspaceConflict("Original evidence was modified")
            if not original.exists():
                with original.open("xb") as stream:
                    stream.write(content)
                original.chmod(0o444)
            record = self.path / "sources" / f"{source.source_id}.json"
            if record.exists():
                if Source.model_validate_json(record.read_text()) != source:
                    raise WorkspaceConflict("Source ID already belongs to different evidence")
            else:
                atomic_json(record, source.model_dump(mode="json"))
            return original

    def validate_fact(self, fact: FinancialFact) -> None:
        source = Source.model_validate_json(
            (self.path / "sources" / f"{fact.source_id}.json").read_text()
        )
        if (
            source.published_on > self.identity.cutoff_date
            or fact.period_end > self.identity.cutoff_date
        ):
            raise ValueError("Fact is outside the information cutoff")
        original = self.path / "originals" / source.sha256
        if (
            not original.exists()
            or hashlib.sha256(original.read_bytes()).hexdigest() != source.sha256
        ):
            raise WorkspaceConflict("Original evidence missing or modified")
        if fact.entity != self.identity.legal_name:
            raise ValueError("Fact belongs to another entity")
        if fact.classification == "reported" and not fact.original_verified:
            raise ValueError("Reported fact requires verification against original evidence")

    def revise(self, section: str, actor: str, data: object, reason: str) -> Path:
        if section not in self.OWNERS:
            raise ValueError("Unknown dossier section")
        owner = self.OWNERS[section]
        if actor not in {"ceo", "research", "accounting", "business", "valuation", "review"}:
            raise PermissionError("Unknown writer")
        if owner is not None and owner != actor:
            raise PermissionError(f"{section} belongs to {owner}; reviewer must file a finding")
        if not reason.strip():
            raise ValueError("Revision requires an explanation")
        with exclusive_lock(self.path / f".{section}.lock"):
            revisions = sorted((self.path / section).glob("v*.json"))
            previous = hashlib.sha256(revisions[-1].read_bytes()).hexdigest() if revisions else None
            destination = self.path / section / f"v{len(revisions) + 1:06d}.json"
            atomic_json(
                destination,
                {
                    "actor": actor,
                    "reason": reason,
                    "created_at": datetime.now(UTC).isoformat(),
                    "previous_sha256": previous,
                    "data": data,
                },
            )
            return destination
