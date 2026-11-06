"""GCR sweep: every metric at every GCR for the pessimistic, central and optimistic cases (spec §12.7)."""

import math
from dataclasses import dataclass
from enum import StrEnum

import numpy as np

from apv_core.constants import (
    DEFAULT_APV_COST_PREMIUM,
    DEFAULT_POLICY_LIMIT,
    DEFAULT_RANGE_SPREAD,
    GCR_GRID,
    KUSUM_A_MAX_MW,
    KUSUM_A_MIN_MW,
    POLICY_LIMIT_MAX,
    POLICY_LIMIT_MIN,
    TOL,
    Season,
)
from apv_core.crops import needs_evidence_notice, relative_yield, season_light
from apv_core.farm import SeasonCrop, baseline_income, revenue_weights, season_farm_income
from apv_core.finance import FinanceInputs, apply_case, kusum_a_per_acre, lease_per_acre, project_flows
from apv_core.ler import economic_ratio, energy_term, ler
from apv_core.notices import Notice, NoticeCode
from apv_core.physics import PhysicsTable, Structure, farmable_fraction, kwp_per_acre
from apv_core.ranges import Case, Range
from apv_core.retention import allowed_gcr, outside_limit, retention


class BusinessModel(StrEnum):
    KUSUM_A = "kusum_a"
    LEASE = "lease"


METRIC_KEYS: tuple[str, ...] = (
    "farm_income",
    "energy_income",
    "total_income",
    "farmer_net_income",
    "ler",
    "energy_term",
    "economic_ratio",
    "npv",
    "kwp_per_acre",
    "energy_kwh_per_acre",
    "payback_years",
    "project_irr",
    "developer_irr",
    "max_affordable_lease",
)


@dataclass(frozen=True)
class SweepInputs:
    physics: PhysicsTable
    structure: Structure
    rotation: tuple[SeasonCrop, ...]
    finance: FinanceInputs
    business_model: BusinessModel
    policy_limit: float = DEFAULT_POLICY_LIMIT
    apv_cost_premium: float = DEFAULT_APV_COST_PREMIUM
    land_acres: float | None = None
    range_spread: float = DEFAULT_RANGE_SPREAD

    def __post_init__(self) -> None:
        object.__setattr__(self, "rotation", tuple(self.rotation))
        seasons = [sc.season for sc in self.rotation]
        if not 1 <= len(seasons) <= 3 or len(set(seasons)) != len(seasons):
            raise ValueError("rotation needs 1-3 crops, at most one per season")
        if not POLICY_LIMIT_MIN <= self.policy_limit <= POLICY_LIMIT_MAX:
            raise ValueError(f"policy_limit must be within [{POLICY_LIMIT_MIN}, {POLICY_LIMIT_MAX}]")
        if not 0 <= self.range_spread < 0.5:
            raise ValueError("range_spread must be in [0, 0.5)")
        if not (math.isfinite(self.apv_cost_premium) and self.apv_cost_premium >= 0):
            raise ValueError("apv_cost_premium must be finite and >= 0")
        if self.land_acres is not None and not (math.isfinite(self.land_acres) and self.land_acres > 0):
            raise ValueError("land_acres must be finite and > 0 when given")


@dataclass(frozen=True)
class SweepResult:
    gcr: tuple[float, ...]
    metrics: dict[str, tuple[Range, ...]]
    retention: dict[Season, tuple[Range, ...]]
    outside_policy: tuple[bool, ...]
    allowed_gcr: Range
    baseline_farm_income: float
    notices: tuple[Notice, ...]


def _run_case(inputs: SweepInputs, case: Case) -> tuple[dict[str, list], dict[Season, np.ndarray], list[str | None]]:
    p, s = inputs.physics, inputs.structure
    f = apply_case(inputs.finance, case, inputs.range_spread)
    gcr = np.array(GCR_GRID)
    a_farm = np.array([farmable_fraction(g, s) for g in GCR_GRID])
    premium = np.where(gcr == 0.0, 0.0, inputs.apv_cost_premium)
    kwp = np.array([kwp_per_acre(g, s.module_efficiency) for g in GCR_GRID])
    kwh_yr1 = p.energy_kwh_per_kwp.sum(axis=1)
    e_term = energy_term(kwp, kwh_yr1, p.ref_energy_kwh_per_acre)

    ret: dict[Season, np.ndarray] = {}
    farm = np.zeros(len(GCR_GRID))
    for sc in inputs.rotation:
        y_rel = relative_yield(season_light(p.light_fraction, sc.season), sc.crop.l_t.get(case), sc.crop.k.get(case))
        ret[sc.season] = retention(a_farm, y_rel)
        farm += season_farm_income(sc.economics, y_rel, a_farm, premium)
    ler_values = ler(revenue_weights(inputs.rotation), ret, e_term)
    baseline = sum(baseline_income(sc.economics) for sc in inputs.rotation)

    out: dict[str, list] = {k: [] for k in METRIC_KEYS}
    irr_reasons: list[str | None] = []
    is_lease = inputs.business_model is BusinessModel.LEASE
    for i in range(len(GCR_GRID)):
        energy_income = float(project_flows(kwp[i], kwh_yr1[i], f)[1])
        kusum = kusum_a_per_acre(kwp[i], kwh_yr1[i], farm[i], f)
        lease = lease_per_acre(kwp[i], kwh_yr1[i], farm[i], f) if is_lease else None
        out["farm_income"].append(float(farm[i]))
        out["energy_income"].append(energy_income)
        out["total_income"].append(float(farm[i]) + energy_income)
        out["farmer_net_income"].append(lease.farmer_income_year1 if lease else kusum.farmer_net_income_year1)
        out["ler"].append(float(ler_values[i]))
        out["energy_term"].append(float(e_term[i]))
        out["economic_ratio"].append(economic_ratio(float(farm[i]), energy_income, baseline))
        out["npv"].append(kusum.npv)
        out["kwp_per_acre"].append(float(kwp[i]))
        out["energy_kwh_per_acre"].append(float(kwp[i] * kwh_yr1[i] * f.availability))
        out["payback_years"].append(kusum.payback_years)
        out["project_irr"].append(kusum.project_irr.value)
        out["developer_irr"].append(lease.developer_irr.value if lease else None)
        out["max_affordable_lease"].append(lease.max_affordable_lease if lease else None)
        irr_reasons.append(kusum.project_irr.reason)
    return out, ret, irr_reasons


def _notices(
    inputs: SweepInputs,
    central: dict[str, list],
    ret: dict[Season, np.ndarray],
    flags: np.ndarray,
    allowed_central: float | None,
    irr_reasons: list[str | None],
) -> list[Notice]:
    notices: list[Notice] = []
    limit = inputs.policy_limit
    for sc in inputs.rotation:
        if needs_evidence_notice(sc.crop):
            extra = " (user-entered parameters)" if sc.crop.user_entered else ""
            notices.append(
                Notice(
                    NoticeCode.LOW_EVIDENCE_CROP,
                    f"{sc.crop.name}: shade-response evidence grade {sc.crop.grade}{extra}; treat yields as rough.",
                )
            )
    if any(sc.crop.user_entered or sc.economics.user_entered for sc in inputs.rotation):
        notices.append(Notice(NoticeCode.USER_ENTERED_VALUES, "Some crop values were entered by the user."))
    if flags.any():
        g = GCR_GRID[int(np.argmax(flags))]
        notices.append(
            Notice(
                NoticeCode.OUTSIDE_POLICY_LIMIT,
                f"GCR {g:.2f} and above drop yield below the proposed {limit:.0%} limit (draft).",
                g,
                tuple(x for x, out in zip(GCR_GRID, flags, strict=True) if out),
            )
        )
    if allowed_central is None:
        failing = [sc.crop.name for sc in inputs.rotation if ret[sc.season][1] < limit - TOL]
        names = " and ".join(failing) or "the rotation"
        notices.append(
            Notice(
                NoticeCode.NO_ALLOWED_GCR,
                f"No panel density in this range keeps {names} at or above {limit:.0%} yield.",
            )
        )
    if inputs.business_model is BusinessModel.KUSUM_A and inputs.land_acres is not None:
        sizes = {g: central["kwp_per_acre"][i] * inputs.land_acres / 1000.0 for i, g in enumerate(GCR_GRID) if i > 0}
        bad = tuple(g for g, mw in sizes.items() if not KUSUM_A_MIN_MW <= mw <= KUSUM_A_MAX_MW)
        if bad:
            listed = ", ".join(f"{g:.2f} ({sizes[g]:.2f} MW)" for g in bad)
            notices.append(
                Notice(
                    NoticeCode.KUSUM_SIZE_OUT_OF_RANGE,
                    f"Plant size is outside PM-KUSUM A's {KUSUM_A_MIN_MW}-{KUSUM_A_MAX_MW} MW range at GCR {listed}.",
                    bad[0],
                    bad,
                )
            )
    bad = tuple(g for i, g in enumerate(GCR_GRID) if i > 0 and central["project_irr"][i] is None)
    if bad:
        reason = irr_reasons[GCR_GRID.index(bad[0])]
        notices.append(
            Notice(NoticeCode.IRR_UNDEFINED, f"{reason} at GCR {', '.join(f'{g:.2f}' for g in bad)}.", bad[0], bad)
        )
    if inputs.business_model is BusinessModel.LEASE:
        bad = tuple(g for i, g in enumerate(GCR_GRID) if i > 0 and central["max_affordable_lease"][i] is None)
        if bad:
            notices.append(
                Notice(
                    NoticeCode.LEASE_NOT_VIABLE,
                    f"Not viable at target IRR at GCR {', '.join(f'{g:.2f}' for g in bad)}.",
                    bad[0],
                    bad,
                )
            )
    return notices


def run_sweep(inputs: SweepInputs) -> SweepResult:
    results = {case: _run_case(inputs, case) for case in Case}
    n = len(GCR_GRID)

    def ranges(get) -> tuple[Range, ...]:
        return tuple(
            Range(get(Case.PESSIMISTIC, i), get(Case.CENTRAL, i), get(Case.OPTIMISTIC, i)) for i in range(n)
        )

    metrics = {k: ranges(lambda c, i, k=k: results[c][0][k][i]) for k in METRIC_KEYS}
    seasons = [sc.season for sc in inputs.rotation]
    ret_ranges = {s: ranges(lambda c, i, s=s: float(results[c][1][s][i])) for s in seasons}
    central_metrics, central_ret, central_reasons = results[Case.CENTRAL]
    flags = outside_limit(central_ret, inputs.policy_limit)
    allowed = Range(*(allowed_gcr(GCR_GRID, results[c][1], inputs.policy_limit) for c in Case))
    return SweepResult(
        gcr=GCR_GRID,
        metrics=metrics,
        retention=ret_ranges,
        outside_policy=tuple(bool(x) for x in flags),
        allowed_gcr=allowed,
        baseline_farm_income=float(sum(baseline_income(sc.economics) for sc in inputs.rotation)),
        notices=tuple(_notices(inputs, central_metrics, central_ret, flags, allowed.central, central_reasons)),
    )
