import hashlib
from datetime import date

import pytest

from ares_research.domain import CompanyIdentity, FinancialFact, Source
from ares_research.extraction import extract_company_fact
from ares_research.storage import Dossier, WorkspaceConflict, exclusive_lock


def identity():
    return CompanyIdentity(
        legal_name="Synthetic SA",
        ticker="SYN",
        exchange="TEST",
        instrument="ordinary_share",
        currency="USD",
        cutoff_date=date(2025, 3, 1),
        accounting_standard="IFRS",
        sector="industrial",
        synthetic=True,
    )


def source(content=b"evidence"):
    return Source(
        source_id="annual",
        url="synthetic://test",
        title="Synthetic source",
        publisher="Test",
        published_on=date(2025, 2, 1),
        retrieved_on=date(2025, 3, 1),
        sha256=hashlib.sha256(content).hexdigest(),
        kind="synthetic",
    )


def test_originals_are_content_addressed_and_conflicting_sources_rejected(tmp_path):
    dossier = Dossier(tmp_path, identity())
    original = dossier.add_source(source(), b"evidence")
    assert dossier.add_source(source(), b"evidence") == original
    with pytest.raises(ValueError, match="checksum"):
        dossier.add_source(source(), b"changed")
    with pytest.raises(WorkspaceConflict):
        dossier.add_source(source().model_copy(update={"title": "changed"}), b"evidence")
    assert len(list((dossier.path / "sources").iterdir())) == 1


def test_cutoff_and_real_synthetic_separation(tmp_path):
    dossier = Dossier(tmp_path, identity())
    with pytest.raises(ValueError, match="Look-ahead"):
        dossier.add_source(
            source().model_copy(update={"published_on": date(2025, 4, 1)}), b"evidence"
        )
    with pytest.raises(ValueError, match="mix"):
        dossier.add_source(source().model_copy(update={"kind": "issuer"}), b"evidence")


def test_revision_ownership_chain_and_lock_recovery(tmp_path):
    dossier = Dossier(tmp_path, identity())
    first = dossier.revise("model", "valuation", {"ev": 100}, "first")
    second = dossier.revise("model", "valuation", {"ev": 120}, "corrected")
    assert hashlib.sha256(first.read_bytes()).hexdigest() in second.read_text()
    with pytest.raises(PermissionError):
        dossier.revise("model", "review", {}, "unauthorized correction")
    with exclusive_lock(tmp_path / "busy.lock"):
        with pytest.raises(WorkspaceConflict):
            with exclusive_lock(tmp_path / "busy.lock"):
                pass


def test_ticker_reuse_does_not_mix_company_contexts():
    first = identity()
    second = first.model_copy(update={"exchange": "OTRA"})
    assert first.case_id != second.case_id


def test_xbrl_restatement_ambiguity_and_future_filing():
    rows = [
        {"start": "2024-01-01", "end": "2024-12-31", "filed": "2025-02-01", "val": 100},
        {"start": "2024-01-01", "end": "2024-12-31", "filed": "2025-04-01", "val": 200},
    ]
    doc = {"facts": {"us-gaap": {"Revenue": {"units": {"USD": rows}}}}}
    arguments = (doc, "us-gaap", "Revenue", "USD", date(2024, 12, 31))
    result = extract_company_fact(*arguments, date(2025, 3, 1), date(2024, 1, 1))
    assert result["value"] == 100 and not result["original_verified"]
    with pytest.raises(ValueError, match="Conflicting"):
        extract_company_fact(*arguments, date(2025, 5, 1), date(2024, 1, 1))


def test_extracted_fact_requires_original_and_entity(tmp_path):
    dossier = Dossier(tmp_path, identity())
    dossier.add_source(source(), b"evidence")
    fact = FinancialFact(
        concept="Assets",
        value=100,
        unit="USD",
        entity="Synthetic SA",
        period_end=date(2024, 12, 31),
        period_type="instant",
        source_id="annual",
        locator="page 1",
    )
    with pytest.raises(ValueError, match="verification"):
        dossier.validate_fact(fact)
    dossier.validate_fact(fact.model_copy(update={"original_verified": True}))
