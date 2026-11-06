"""PM-KUSUM A and land-lease cash flows per acre (spec §12.6; REQ-FIN-01..06).

All money is ₹ per acre (or per kWp where named). Year 0 is construction; years 1..N operate.
"""

import dataclasses
import math
from dataclasses import dataclass

import numpy as np

from apv_core.cashflow import IrrResult, annuity_payment, escalating_annuity_factor, irr, npv, simple_payback
from apv_core.constants import ANALYSIS_YEARS
from apv_core.ranges import Case

LEASE_NOT_VIABLE = "Not viable at target IRR"


@dataclass(frozen=True)
class FinanceInputs:
    capex_per_kwp: float
    om_per_kwp_year: float
    om_escalation: float
    tariff_per_kwh: float
    degradation: float
    availability: float
    debt_share: float
    interest_rate: float
    loan_years: int
    discount_rate: float
    crop_inflation: float
    lease_per_acre_year: float
    lease_escalation: float
    target_irr: float
    years: int = ANALYSIS_YEARS

    def __post_init__(self) -> None:
        for field in dataclasses.fields(self):
            if not math.isfinite(getattr(self, field.name)):
                raise ValueError(f"{field.name} must be a finite number")
        checks = [
            (self.capex_per_kwp > 0, "capex_per_kwp must be > 0"),
            (self.tariff_per_kwh > 0, "tariff_per_kwh must be > 0"),
            (self.om_per_kwp_year >= 0, "om_per_kwp_year must be >= 0"),
            (0 <= self.degradation < 0.05, "degradation must be in [0, 0.05)"),
            (0 < self.availability <= 1, "availability must be in (0, 1]"),
            (0 <= self.debt_share <= 0.9, "debt_share must be in [0, 0.9]"),
            (self.years >= 1, "years must be >= 1"),
            (1 <= self.loan_years <= self.years, "loan_years must be in [1, years]"),
            (self.lease_per_acre_year >= 0, "lease_per_acre_year must be >= 0"),
        ]
        rates = ("om_escalation", "interest_rate", "discount_rate", "crop_inflation", "lease_escalation", "target_irr")
        checks += [(getattr(self, r) > -1, f"{r} must be > -1") for r in rates]
        for ok, message in checks:
            if not ok:
                raise ValueError(message)


@dataclass(frozen=True)
class KusumAResult:
    project_irr: IrrResult
    npv: float
    payback_years: float | None
    farmer_net_income_year1: float


@dataclass(frozen=True)
class LeaseResult:
    developer_irr: IrrResult
    farmer_income_year1: float
    max_affordable_lease: float | None
    max_lease_reason: str | None


def apply_case(f: FinanceInputs, case: Case, spread: float) -> FinanceInputs:
    """Pessimistic: lower tariff, higher CAPEX. Optimistic: the reverse. Central: unchanged."""
    if case is Case.CENTRAL:
        return f
    sign = -1.0 if case is Case.PESSIMISTIC else 1.0
    return dataclasses.replace(
        f,
        tariff_per_kwh=f.tariff_per_kwh * (1 + sign * spread),
        capex_per_kwp=f.capex_per_kwp * (1 - sign * spread),
    )


def energy_series(kwh_per_kwp_year1: float, f: FinanceInputs) -> np.ndarray:
    t = np.arange(1, f.years + 1)
    return kwh_per_kwp_year1 * f.availability * (1 - f.degradation) ** (t - 1)


def project_flows(kwp: float, kwh_per_kwp_year1: float, f: FinanceInputs) -> np.ndarray:
    """Unlevered energy-investment flows per acre (farm income excluded)."""
    t = np.arange(1, f.years + 1)
    revenue = kwp * energy_series(kwh_per_kwp_year1, f) * f.tariff_per_kwh
    om = kwp * f.om_per_kwp_year * (1 + f.om_escalation) ** (t - 1)
    return np.concatenate([[-f.capex_per_kwp * kwp], revenue - om])


def kusum_a_per_acre(kwp: float, kwh_per_kwp_year1: float, farm_income_year1: float, f: FinanceInputs) -> KusumAResult:
    flows = project_flows(kwp, kwh_per_kwp_year1, f)
    debt = f.debt_share * f.capex_per_kwp * kwp
    service = annuity_payment(debt, f.interest_rate, f.loan_years)
    return KusumAResult(
        project_irr=irr(flows),
        npv=npv(f.discount_rate, flows),
        payback_years=simple_payback(flows),
        farmer_net_income_year1=farm_income_year1 + float(flows[1]) - service,
    )


def max_affordable_lease(flows: np.ndarray, f: FinanceInputs) -> tuple[float | None, str | None]:
    """Year-1 lease (escalating) that brings the developer exactly to target IRR; closed form."""
    lease = npv(f.target_irr, flows) / escalating_annuity_factor(f.target_irr, f.lease_escalation, f.years)
    if lease <= 0:
        return None, LEASE_NOT_VIABLE
    return lease, None


def lease_per_acre(kwp: float, kwh_per_kwp_year1: float, farm_income_year1: float, f: FinanceInputs) -> LeaseResult:
    flows = project_flows(kwp, kwh_per_kwp_year1, f)
    lease_year1 = f.lease_per_acre_year if kwp > 0 else 0.0  # no plant, no lease
    t = np.arange(1, f.years + 1)
    developer = flows.copy()
    developer[1:] -= lease_year1 * (1 + f.lease_escalation) ** (t - 1)
    lease_max, reason = max_affordable_lease(flows, f)
    return LeaseResult(
        developer_irr=irr(developer),
        farmer_income_year1=lease_year1 + farm_income_year1,
        max_affordable_lease=lease_max,
        max_lease_reason=reason,
    )
