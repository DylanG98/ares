from decimal import Decimal as D

import pytest
from pydantic import ValidationError

from ares_research.domain import ValuationInputs
from ares_research.finance import DcfModel, average_balance_return, ratio
from ares_research.review import IndependentReviewer
from ares_research.smoke import synthetic_inputs


def test_known_perpetuity_and_equity_bridge():
    data = synthetic_inputs().model_dump()
    data.update(
        debt=200,
        cash=50,
        non_operating_assets=10,
        minority_interest=5,
        revenue=1000,
        diluted_shares=100,
        shares_per_instrument=2,
    )
    for s in data["scenarios"]:
        s.update(
            revenue_growth=[D(0)] * 5,
            ebit_margin=D(".2"),
            tax_rate=D(".25"),
            da_to_sales=D(".03"),
            capex_to_sales=D(".03"),
            terminal_growth=D(0),
            wacc=D(".1"),
        )
    inputs = ValuationInputs.model_validate(data)
    result = DcfModel(inputs).calculate(inputs.scenarios[1])
    # 150 FCFF forever / 10% = 1500 EV; equity 1355 / 100 shares * 2 per ADR.
    assert result.enterprise_value == pytest.approx(D(1500))
    assert result.per_instrument == pytest.approx(D("27.10"))
    assert IndependentReviewer().recalculate(inputs, inputs.scenarios[1]) == pytest.approx(27.10)


def test_missing_and_average_balance():
    assert ratio(None, D(10)) is None
    assert ratio(D(10), D(0)) is None
    assert average_balance_return(D(20), D(100), D(300)) == D(".1")
    assert average_balance_return(D(20), None, D(300)) is None


@pytest.mark.parametrize(
    "field,value",
    [("rate_basis", "real"), ("diluted_shares", 0), ("sector", "bank"), ("lease_liabilities", 10)],
)
def test_invalid_financial_assumptions(field, value):
    data = synthetic_inputs().model_dump()
    data[field] = value
    with pytest.raises(ValidationError):
        ValuationInputs.model_validate(data)


def test_terminal_guard_and_duplicate_scenario():
    data = synthetic_inputs().model_dump()
    data["scenarios"][0]["terminal_growth"] = data["scenarios"][0]["wacc"]
    with pytest.raises(ValidationError):
        ValuationInputs.model_validate(data)
    data = synthetic_inputs().model_dump()
    data["scenarios"][0]["name"] = "base"
    with pytest.raises(ValidationError):
        ValuationInputs.model_validate(data)


def test_independent_reviewer_rejects_corruption_and_self_review():
    inputs = synthetic_inputs()
    observed = {
        s.name: float(DcfModel(inputs).calculate(s).per_instrument) for s in inputs.scenarios
    }
    reviewer = IndependentReviewer()
    assert reviewer.check_values(inputs, observed) == []
    observed["base"] *= 1.1
    findings = reviewer.check_values(inputs, observed)
    assert len(findings) == 1
    with pytest.raises(ValueError):
        reviewer.assert_publishable("modeler", "reviewer", findings, ["model-sha"])
    with pytest.raises(PermissionError):
        reviewer.assert_publishable("same", "same", [], ["model-sha"])
