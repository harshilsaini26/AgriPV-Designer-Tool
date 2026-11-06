"""Land equivalent ratio and economic ratio (spec §12.5)."""

from collections.abc import Mapping

import numpy as np

from apv_core.constants import Season


def energy_term(
    kwp_per_acre: np.ndarray, annual_kwh_per_kwp: np.ndarray, ref_energy_kwh_per_acre: float
) -> np.ndarray:
    """APV energy per acre relative to the reference conventional PV plant on one acre."""
    return np.asarray(kwp_per_acre, dtype=float) * np.asarray(annual_kwh_per_kwp, dtype=float) / ref_energy_kwh_per_acre


def ler(
    weights: Mapping[Season, float],
    retention_by_season: Mapping[Season, np.ndarray],
    energy_term: np.ndarray,
) -> np.ndarray:
    """LER = revenue-weighted agri retention + energy term."""
    agri = sum(w * np.asarray(retention_by_season[s], dtype=float) for s, w in weights.items())
    return agri + np.asarray(energy_term, dtype=float)


def economic_ratio(farm_income: float, energy_income: float, baseline_farm_income: float) -> float | None:
    """(farm + energy income) / baseline farm income; None when the baseline is not positive."""
    if baseline_farm_income <= 0:
        return None
    return (farm_income + energy_income) / baseline_farm_income
