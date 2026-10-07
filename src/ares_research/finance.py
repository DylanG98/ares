"""Deterministic FCFF valuation. Decimal arithmetic, explicit terminal reinvestment."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .domain import Scenario, ValuationInputs

D = Decimal


def ratio(numerator: Decimal | None, denominator: Decimal | None) -> Decimal | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def average_balance_return(
    profit: Decimal | None, opening: Decimal | None, closing: Decimal | None
) -> Decimal | None:
    if opening is None or closing is None:
        return None
    return ratio(profit, (opening + closing) / 2)


@dataclass(frozen=True)
class Projection:
    year: int
    revenue: Decimal
    ebit: Decimal
    nopat: Decimal
    depreciation: Decimal
    capex: Decimal
    delta_nwc: Decimal
    fcff: Decimal
    present_value: Decimal


@dataclass(frozen=True)
class Valuation:
    scenario: str
    projections: tuple[Projection, ...]
    terminal_cashflow: Decimal
    terminal_value: Decimal
    terminal_present_value: Decimal
    enterprise_value: Decimal
    equity_value: Decimal
    per_share: Decimal
    per_instrument: Decimal
    terminal_weight: Decimal | None


class DcfModel:
    def __init__(self, inputs: ValuationInputs):
        self.inputs = inputs

    def calculate(self, scenario: Scenario) -> Valuation:
        previous_revenue = self.inputs.revenue
        projections = []
        for year, growth in enumerate(scenario.revenue_growth, 1):
            revenue = previous_revenue * (1 + growth)
            ebit = revenue * scenario.ebit_margin
            nopat = ebit * (1 - scenario.tax_rate)
            depreciation = revenue * scenario.da_to_sales
            capex = revenue * scenario.capex_to_sales
            delta_nwc = (revenue - previous_revenue) * scenario.nwc_to_sales
            fcff = nopat + depreciation - capex - delta_nwc
            pv = fcff / (1 + scenario.wacc) ** year
            projections.append(
                Projection(year, revenue, ebit, nopat, depreciation, capex, delta_nwc, fcff, pv)
            )
            previous_revenue = revenue
        # Sustainable terminal growth requires reinvestment g / ROIC, not an unexplained FCF bump.
        terminal_nopat = projections[-1].nopat * (1 + scenario.terminal_growth)
        terminal_cashflow = terminal_nopat * (1 - scenario.terminal_growth / scenario.terminal_roic)
        terminal_value = terminal_cashflow / (scenario.wacc - scenario.terminal_growth)
        terminal_pv = terminal_value / (1 + scenario.wacc) ** len(projections)
        ev = sum((p.present_value for p in projections), D(0)) + terminal_pv
        equity = (
            ev
            - self.inputs.debt
            - self.inputs.lease_liabilities
            + self.inputs.cash
            + self.inputs.non_operating_assets
            - self.inputs.minority_interest
        )
        per_share = equity / self.inputs.diluted_shares
        return Valuation(
            scenario.name,
            tuple(projections),
            terminal_cashflow,
            terminal_value,
            terminal_pv,
            ev,
            equity,
            per_share,
            per_share * self.inputs.shares_per_instrument,
            ratio(terminal_pv, ev),
        )
