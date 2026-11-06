import dataclasses

import numpy as np
import pytest
from fixtures import finance_defaults

from apv_core.cashflow import irr
from apv_core.finance import (
    apply_case,
    kusum_a_per_acre,
    lease_per_acre,
    max_affordable_lease,
    project_flows,
)
from apv_core.ranges import Case


def test_project_flows_reference_case():
    f = dataclasses.replace(
        finance_defaults(), degradation=0.0, om_escalation=0.0, availability=1.0, years=2, loan_years=2
    )
    flows = project_flows(kwp=100.0, kwh_per_kwp_year1=1500.0, f=f)
    assert flows[0] == pytest.approx(-100.0 * f.capex_per_kwp)
    assert flows[1] == pytest.approx(100 * 1500 * f.tariff_per_kwh - 100 * f.om_per_kwp_year)
    assert len(flows) == 3


def test_kusum_a_farmer_income_includes_debt_service():
    f = finance_defaults()
    r = kusum_a_per_acre(kwp=261.0, kwh_per_kwp_year1=1500.0, farm_income_year1=40000.0, f=f)
    assert r.project_irr.value is not None and 0.0 < r.project_irr.value < 0.5
    assert r.payback_years is not None and r.payback_years < f.years
    flows = project_flows(261.0, 1500.0, f)
    debt = f.debt_share * f.capex_per_kwp * 261.0
    service = debt * f.interest_rate / (1 - (1 + f.interest_rate) ** -f.loan_years)
    assert r.farmer_net_income_year1 == pytest.approx(40000.0 + flows[1] - service)


def test_max_lease_closed_form_matches_numeric():
    f = finance_defaults()
    flows = project_flows(261.0, 1500.0, f)
    lease, reason = max_affordable_lease(flows, f)
    assert reason is None and lease > 0
    t = np.arange(1, f.years + 1)
    dev = flows.copy()
    dev[1:] -= lease * (1 + f.lease_escalation) ** (t - 1)
    assert irr(dev).value == pytest.approx(f.target_irr, abs=1e-6)


def test_max_lease_not_viable():
    f = dataclasses.replace(finance_defaults(), target_irr=0.60)
    assert max_affordable_lease(project_flows(261.0, 1500.0, f), f) == (None, "Not viable at target IRR")


def test_zero_capacity_never_raises():
    r = kusum_a_per_acre(0.0, 0.0, 40000.0, finance_defaults())
    assert r.project_irr.value is None and r.payback_years is None
    assert r.farmer_net_income_year1 == pytest.approx(40000.0)
    lr = lease_per_acre(0.0, 0.0, 40000.0, finance_defaults())
    assert lr.developer_irr.value is None and lr.max_affordable_lease is None


def test_lease_farmer_income():
    r = lease_per_acre(261.0, 1500.0, 40000.0, finance_defaults())
    assert r.farmer_income_year1 == pytest.approx(finance_defaults().lease_per_acre_year + 40000.0)
    assert r.developer_irr.value is not None


def test_apply_case_spreads_tariff_and_capex():
    f = finance_defaults()
    p = apply_case(f, Case.PESSIMISTIC, 0.10)
    assert p.tariff_per_kwh == pytest.approx(f.tariff_per_kwh * 0.9)
    assert p.capex_per_kwp == pytest.approx(f.capex_per_kwp * 1.1)
    o = apply_case(f, Case.OPTIMISTIC, 0.10)
    assert o.tariff_per_kwh == pytest.approx(f.tariff_per_kwh * 1.1)
    assert apply_case(f, Case.CENTRAL, 0.10) == f


def test_finance_inputs_reject_nonpositive():
    for field in ("capex_per_kwp", "tariff_per_kwh"):
        with pytest.raises(ValueError):
            dataclasses.replace(finance_defaults(), **{field: 0.0})
