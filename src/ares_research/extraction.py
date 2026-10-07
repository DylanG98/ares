"""Bounded PDF and SEC companyfacts extraction; extraction is not validation."""

from datetime import date
from pathlib import Path

from pypdf import PdfReader


def extract_pdf(path: Path) -> list[dict]:
    if path.stat().st_size > 50 * 1024 * 1024:
        raise ValueError("PDF exceeds 50 MiB; split and review before extraction")
    reader = PdfReader(path)
    if reader.is_encrypted:
        raise ValueError("Encrypted PDF requires authorized access")
    pages = [
        {"page": i, "text": page.extract_text() or ""} for i, page in enumerate(reader.pages, 1)
    ]
    if not any(p["text"].strip() for p in pages):
        raise ValueError("No text layer: OCR required; no financial values inferred")
    return pages


def extract_company_fact(
    document: dict,
    taxonomy: str,
    concept: str,
    unit: str,
    period_end: date,
    cutoff: date,
    period_start: date | None = None,
) -> dict:
    values = document["facts"][taxonomy][concept]["units"][unit]
    matches = [
        v
        for v in values
        if date.fromisoformat(v["end"]) == period_end
        and date.fromisoformat(v["filed"]) <= cutoff
        and v.get("start") == (period_start.isoformat() if period_start else None)
    ]
    if not matches:
        raise ValueError("No matching XBRL fact public at cutoff")
    if len({str(v["val"]) for v in matches}) != 1:
        raise ValueError("Conflicting/restated XBRL facts: inspect originals and select explicitly")
    return {
        "entity": document.get("entityName"),
        "cik": document.get("cik"),
        "concept": f"{taxonomy}:{concept}",
        "unit": unit,
        "value": matches[0]["val"],
        "period_start": period_start.isoformat() if period_start else None,
        "period_end": period_end.isoformat(),
        "filings": matches,
        "original_verified": False,
        "status": "extracted_requires_original_validation",
    }
