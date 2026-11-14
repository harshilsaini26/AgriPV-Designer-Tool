"""Panel temperature and conversion of light to grid power, per kWp of panels (design spec §5.3)."""

import numpy as np

from apv_physics.inputs import Losses

FAIMAN_U0 = 25.0  # W/m2/K
FAIMAN_U1 = 6.84  # W/m2/K per m/s of wind
INVERTER_REFERENCE_EFFICIENCY = 0.9637  # PVWatts reference inverter


def cell_temperature(g_eff, temp_air, wind_speed) -> np.ndarray:
    """Cell temperature in deg C (Faiman model, open rack)."""
    return np.asarray(temp_air, dtype=float) + np.asarray(g_eff, dtype=float) / (
        FAIMAN_U0 + FAIMAN_U1 * np.asarray(wind_speed, dtype=float)
    )


def dc_power_per_kwp(g_eff, temp_cell, temp_coeff_per_c: float) -> np.ndarray:
    """DC power in W per kWp of panels, before losses (PVWatts)."""
    power = np.asarray(g_eff, dtype=float) * (
        1 + temp_coeff_per_c * (np.asarray(temp_cell, dtype=float) - 25.0)
    )
    return np.maximum(power, 0.0)


def ac_power_per_kwp(p_dc, losses: Losses) -> np.ndarray:
    """AC power in W per kWp of panels: DC losses, then the PVWatts inverter with clipping, then AC losses."""
    p = np.asarray(p_dc, dtype=float) * losses.dc_factor
    pac0 = 1000.0 / losses.dc_ac_ratio  # the inverter's AC rating per kWp of panels
    pdc0 = pac0 / losses.inverter_efficiency
    zeta = p / pdc0
    with np.errstate(divide="ignore", invalid="ignore"):
        eta = (
            losses.inverter_efficiency
            / INVERTER_REFERENCE_EFFICIENCY
            * (-0.0162 * zeta - 0.0059 / zeta + 0.9858)
        )
        ac = np.minimum(eta * p, pac0)
    ac = np.where(p > 0, ac, 0.0)
    return np.maximum(ac, 0.0) * losses.ac_factor
