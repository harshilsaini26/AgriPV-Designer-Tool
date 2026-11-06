"""Crop economics and farm income per acre (spec §12.4)."""

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from apv_core.constants import Season
from apv_core.crops import CropParams


@dataclass(frozen=True)
class CropEconomics:
    yield_q_per_acre: float
    price_per_q: float
    cost_per_acre: float
    user_entered: bool = False

    def __post_init__(self) -> None:
        values = (self.yield_q_per_acre, self.price_per_q, self.cost_per_acre)
        if not all(math.isfinite(v) and v >= 0 for v in values):
            raise ValueError("crop yield, price and cost must be finite and >= 0")


@dataclass(frozen=True)
class SeasonCrop:
    season: Season
    crop: CropParams
    economics: CropEconomics

    def __post_init__(self) -> None:
        if self.season not in self.crop.seasons:
            raise ValueError(f"crop {self.crop.id!r} is not grown in {self.season}")


def baseline_income(econ: CropEconomics) -> float:
    """Open-field net income per acre."""
    return econ.yield_q_per_acre * econ.price_per_q - econ.cost_per_acre


def season_farm_income(
    econ: CropEconomics, y_rel: np.ndarray, a_farm: np.ndarray | float, apv_cost_premium: float
) -> np.ndarray:
    """Net farm income per acre under APV. Callers pass apv_cost_premium = 0 at GCR 0."""
    y_rel = np.asarray(y_rel, dtype=float)
    a_farm = np.asarray(a_farm, dtype=float)
    revenue = econ.yield_q_per_acre * y_rel * a_farm * econ.price_per_q
    cost = econ.cost_per_acre * a_farm * (1.0 + apv_cost_premium)
    return revenue - cost


def revenue_weights(rotation: Sequence[SeasonCrop]) -> dict[Season, float]:
    """Each season's share of baseline gross crop revenue (sums to 1)."""
    seasons = [sc.season for sc in rotation]
    if len(set(seasons)) != len(seasons):
        raise ValueError("rotation has more than one crop in the same season")
    gross = {sc.season: sc.economics.yield_q_per_acre * sc.economics.price_per_q for sc in rotation}
    total = sum(gross.values())
    if total <= 0:
        raise ValueError("rotation has zero baseline gross revenue; cannot weight seasons")
    return {s: v / total for s, v in gross.items()}
