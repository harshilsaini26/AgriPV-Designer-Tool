"""Cash-flow primitives. In every function flows[0] is at t = 0. Never returns NaN or inf."""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

_IRR_LO, _IRR_HI, _IRR_TOL = -0.99, 10.0, 1e-10


@dataclass(frozen=True)
class IrrResult:
    value: float | None
    reason: str | None


def npv(rate: float, flows: Sequence[float]) -> float:
    f = np.asarray(flows, dtype=float)
    return float(np.sum(f / (1.0 + rate) ** np.arange(len(f))))


def irr(flows: Sequence[float]) -> IrrResult:
    f = np.asarray(flows, dtype=float)
    if not (np.any(f > 0) and np.any(f < 0)):
        return IrrResult(None, "IRR undefined: cash flows never change sign")
    lo, hi = _IRR_LO, _IRR_HI
    f_lo, f_hi = npv(lo, f), npv(hi, f)
    if f_lo == 0:
        return IrrResult(lo, None)
    if np.sign(f_lo) == np.sign(f_hi):
        return IrrResult(None, "IRR undefined: no solution between -99% and 1000%")
    while hi - lo > _IRR_TOL:
        mid = (lo + hi) / 2.0
        f_mid = npv(mid, f)
        if f_mid == 0:
            return IrrResult(mid, None)
        if np.sign(f_mid) == np.sign(f_lo):
            lo, f_lo = mid, f_mid
        else:
            hi = mid
    return IrrResult((lo + hi) / 2.0, None)


def simple_payback(flows: Sequence[float]) -> float | None:
    """Years until cumulative cash flow reaches zero, interpolated within the year."""
    f = np.asarray(flows, dtype=float)
    if f[0] >= 0:
        return None
    cumulative = f[0]
    for t in range(1, len(f)):
        if f[t] > 0 and cumulative + f[t] >= 0:
            return (t - 1) + (-cumulative / f[t])
        cumulative += f[t]
    return None


def escalating_annuity_factor(rate: float, growth: float, years: int) -> float:
    t = np.arange(1, years + 1)
    return float(np.sum((1.0 + growth) ** (t - 1) / (1.0 + rate) ** t))


def annuity_payment(principal: float, rate: float, years: int) -> float:
    if rate == 0:
        return principal / years
    return principal * rate / (1.0 - (1.0 + rate) ** -years)
