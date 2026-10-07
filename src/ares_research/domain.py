"""Validated financial inputs. Missing values remain missing, never implicit zeroes."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from hashlib import sha256
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class CompanyIdentity(StrictModel):
    legal_name: str = Field(min_length=2)
    ticker: str = Field(min_length=1)
    exchange: str = Field(min_length=2)
    regulatory_id: str | None = None
    instrument: Literal["ordinary_share", "adr", "bond", "other"]
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    cutoff_date: date
    market_price_date: date | None = None
    accounting_standard: str = Field(min_length=2)
    sector: str = Field(min_length=2)
    synthetic: bool = False

    @model_validator(mode="after")
    def validate_dates(self):
        if self.market_price_date and self.market_price_date > self.cutoff_date:
            raise ValueError("Market price cannot come from after the analysis cutoff")
        if any(
            "COMPLETAR" in v
            for v in [
                self.legal_name,
                self.ticker,
                self.exchange,
                self.sector,
                self.accounting_standard,
            ]
        ):
            raise ValueError("Complete the request template before submitting")
        return self

    @property
    def case_id(self) -> str:
        # All identity dimensions participate; a reused ticker cannot mix dossiers.
        return sha256(self.model_dump_json().encode()).hexdigest()[:24]


class Source(StrictModel):
    source_id: str = Field(pattern=r"^[a-zA-Z0-9_-]+$")
    url: str = Field(pattern=r"^(https://|synthetic://)")
    title: str
    publisher: str
    published_on: date
    retrieved_on: date
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    kind: Literal["regulator", "issuer", "secondary", "synthetic"]


class FinancialFact(StrictModel):
    concept: str
    value: Decimal | None
    unit: str
    currency: str | None = None
    entity: str
    segment: str = "consolidated"
    period_start: date | None = None
    period_end: date
    period_type: Literal["instant", "annual", "quarter", "ytd", "ttm"]
    source_id: str = Field(pattern=r"^[a-zA-Z0-9_-]+$")
    locator: str = Field(min_length=1)
    classification: Literal["reported", "guidance", "consensus", "assumption"] = "reported"
    adjustment: Decimal | None = None
    adjustment_reason: str | None = None
    original_verified: bool = False

    @model_validator(mode="after")
    def validate_period(self):
        if self.period_type != "instant" and self.period_start is None:
            raise ValueError("Duration facts require period_start")
        if self.period_start and self.period_start > self.period_end:
            raise ValueError("Invalid period")
        if self.adjustment is not None and not self.adjustment_reason:
            raise ValueError("Adjustments require an explicit bridge explanation")
        return self


class Scenario(StrictModel):
    name: Literal["adverso", "base", "favorable"]
    narrative: str = Field(min_length=10)
    revenue_growth: list[Decimal] = Field(min_length=3, max_length=10)
    ebit_margin: Decimal = Field(gt=0, lt=1)
    tax_rate: Decimal = Field(ge=0, lt=1)
    da_to_sales: Decimal = Field(ge=0, lt=1)
    capex_to_sales: Decimal = Field(ge=0, lt=1)
    nwc_to_sales: Decimal = Field(ge=0, lt=1)
    wacc: Decimal = Field(gt=0, lt=1)
    terminal_growth: Decimal = Field(gt=-1, lt=1)
    terminal_roic: Decimal = Field(gt=0, lt=1)

    @model_validator(mode="after")
    def coherent_terminal(self):
        if self.wacc <= self.terminal_growth:
            raise ValueError("WACC must exceed terminal growth")
        if self.terminal_growth < 0 or self.terminal_growth >= self.terminal_roic:
            raise ValueError("This steady-state model requires 0 <= g < terminal ROIC")
        if any(g <= -1 for g in self.revenue_growth):
            raise ValueError("Revenue growth must exceed -100%")
        return self


class ValuationInputs(StrictModel):
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    basis: Literal["nominal", "real"]
    rate_basis: Literal["nominal", "real"]
    sector: str
    revenue: Decimal = Field(gt=0)
    debt: Decimal = Field(ge=0)
    cash: Decimal = Field(ge=0)
    non_operating_assets: Decimal = Field(ge=0)
    minority_interest: Decimal = Field(ge=0)
    diluted_shares: Decimal = Field(gt=0)
    shares_per_instrument: Decimal = Field(gt=0)
    lease_treatment: Literal["operating_in_cashflows", "debt_in_bridge"]
    lease_liabilities: Decimal = Field(ge=0)
    source_ids: list[str] = Field(min_length=1)
    scenarios: list[Scenario] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def coherent(self):
        if self.basis != self.rate_basis:
            raise ValueError("Cash flow and discount rate bases must match")
        if self.sector.casefold() in {"bank", "banking", "insurance", "banco", "aseguradora"}:
            raise ValueError(
                "Use a documented sector-specific model, not this industrial FCFF template"
            )
        if {s.name for s in self.scenarios} != {"adverso", "base", "favorable"}:
            raise ValueError("Exactly one of each scenario is required")
        if self.lease_treatment == "operating_in_cashflows" and self.lease_liabilities != 0:
            raise ValueError(
                "Do not also subtract lease liabilities when leases are in operating cashflows"
            )
        return self
