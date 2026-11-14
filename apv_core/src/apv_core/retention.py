"""Yield retention against the draft policy limit (spec §12.4, §12.7; REQ-POL-01..04).

Provisional definitions pending open questions Q-02 / Q-03:
- retention is measured per acre of land (a_farm × Y_rel) by default, or per cropped area (Y_rel) as an
  option (Japan's basis: the farmland under the panels, with the posts excluded), and
- the limit is checked separately for every season in the rotation.
"""

from collections.abc import Mapping, Sequence
from enum import StrEnum

import numpy as np

from apv_core.constants import POLICY_LIMIT_MAX, POLICY_LIMIT_MIN, TOL, Season


class RetentionBasis(StrEnum):
    """What the policy limit is measured against (Q-02)."""

    LAND = "per_acre_of_land"  # a_farm × Y_rel: crop lost to posts and tracks counts (default, stricter)
    CROPPED_AREA = "per_cropped_area"  # Y_rel: only the shade effect on the area still farmed


def retention(
    a_farm: np.ndarray | float, y_rel: np.ndarray, basis: RetentionBasis = RetentionBasis.LAND
) -> np.ndarray:
    """The single definition of yield retention (Q-02). LER and farm income always use the LAND basis."""
    y = np.asarray(y_rel, dtype=float)
    if basis is RetentionBasis.CROPPED_AREA:
        return np.broadcast_to(y, np.broadcast_shapes(np.shape(a_farm), y.shape)).copy()
    return np.asarray(a_farm, dtype=float) * y


def _check(retention_by_season: Mapping[Season, np.ndarray], limit: float) -> None:
    if not POLICY_LIMIT_MIN <= limit <= POLICY_LIMIT_MAX:
        raise ValueError(f"policy limit must be within [{POLICY_LIMIT_MIN}, {POLICY_LIMIT_MAX}]")
    if not retention_by_season:
        raise ValueError("retention_by_season must contain at least one season")


def _passes(retention_by_season: Mapping[Season, np.ndarray], limit: float) -> np.ndarray:
    _check(retention_by_season, limit)
    stacked = np.vstack([np.asarray(r, dtype=float) for r in retention_by_season.values()])
    return np.all(stacked >= limit - TOL, axis=0)


def outside_limit(retention_by_season: Mapping[Season, np.ndarray], limit: float) -> np.ndarray:
    """True per GCR where any season falls below the limit (Q-03: per season)."""
    return ~_passes(retention_by_season, limit)


def allowed_gcr(
    gcr: Sequence[float], retention_by_season: Mapping[Season, np.ndarray], limit: float
) -> float | None:
    """Largest GCR whose own and every lower GCR pass in every season; None if GCR 0.05 already fails."""
    passes = _passes(retention_by_season, limit)
    run = int(np.argmin(passes)) if not passes.all() else len(passes)
    return None if run <= 1 else gcr[run - 1]
