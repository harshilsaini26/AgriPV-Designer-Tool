"""Run the physics for one district and layout at every panel density (design spec §5.2)."""

import math
from dataclasses import dataclass

import numpy as np
from apv_core.constants import GCR_GRID
from apv_core.physics import PhysicsTable, kwp_per_acre

from apv_physics.ground import farmed_mask, ground_light
from apv_physics.inputs import Kind, Layout, Losses, Module, Weather
from apv_physics.irradiance import effective_irradiance, panel_irradiance
from apv_physics.power import ac_power_per_kwp, cell_temperature, dc_power_per_kwp
from apv_physics.tracking import tracker_rotation

# The conventional ground-mounted plant that LER compares against (parent spec §12.1)
REFERENCE_GCR = 0.45
REFERENCE_TILT_RANGE_DEG = (10.0, 25.0)
REFERENCE_COLLECTOR_WIDTH_M = 4.56
REFERENCE_CENTER_HEIGHT_M = 1.5
TRACKER_REF_AZIMUTH_DEG = 270.0  # a positive tracker rotation faces west


@dataclass(frozen=True)
class PhysicsResult:
    """Monthly results per density. Row 0 of every array is the open field (GCR 0)."""

    table: PhysicsTable
    light_darkest_tenth: np.ndarray  # (11, 12): light on the darkest tenth of the farmed ground
    clear_gap_m: np.ndarray  # (11,): open ground between adjacent rows


def _monthly_energy(
    weather: Weather,
    surface_tilt,
    surface_azimuth,
    gcr: float,
    height: float,
    pitch: float,
    module: Module,
    losses: Losses,
) -> np.ndarray:
    """AC energy per kWp of panels for each month, in kWh."""
    parts = panel_irradiance(
        surface_tilt, surface_azimuth, weather.zenith, weather.azimuth, gcr, height, pitch,
        weather.ghi, weather.dhi, weather.dni, weather.dni_extra, losses.albedo,
    )  # fmt: skip
    g_eff = effective_irradiance(parts, surface_tilt, module.bifaciality, losses.rear_shading)
    if not np.isfinite(g_eff).all():  # never let a NaN turn silently into zero energy further down
        raise FloatingPointError("the irradiance on the panels is not finite for this layout")
    temp_cell = cell_temperature(g_eff, weather.temp_air, weather.wind_speed)
    ac = ac_power_per_kwp(dc_power_per_kwp(g_eff, temp_cell, module.temp_coeff_per_c), losses)
    return np.bincount(weather.month - 1, weights=ac, minlength=12) / 1000.0


def reference_energy_kwh_per_acre(weather: Weather, module: Module, losses: Losses | None = None) -> float:
    """Yearly energy per acre of a conventional fixed-tilt plant in the same district, with the same module."""
    losses = losses or Losses()
    tilt = float(np.clip(weather.optimum_tilt_deg, *REFERENCE_TILT_RANGE_DEG))
    pitch = REFERENCE_COLLECTOR_WIDTH_M / REFERENCE_GCR
    energy = _monthly_energy(
        weather, tilt, 180.0, REFERENCE_GCR, REFERENCE_CENTER_HEIGHT_M, pitch, module, losses
    )
    return float(energy.sum() * kwp_per_acre(REFERENCE_GCR, module.efficiency))


def simulate(weather: Weather, layout: Layout, losses: Losses | None = None) -> PhysicsResult:
    """Monthly energy, ground light and light evenness for `layout` at every density in GCR_GRID."""
    losses = losses or Losses()
    n = len(GCR_GRID)
    energy = np.zeros((n, 12))
    light = np.ones((n, 12))
    darkest = np.ones((n, 12))
    gap = np.full(n, math.inf)
    width, height = layout.collector_width_m, layout.center_height_m

    for i, gcr in enumerate(GCR_GRID):
        if i == 0:
            continue  # the open field: no panels, full light
        pitch = width / gcr
        mask = np.ones(100, dtype=bool)
        if layout.kind is Kind.TRACKER:
            rotation = tracker_rotation(weather.zenith, weather.azimuth, gcr, layout.max_angle_deg)
            ref_azimuth = TRACKER_REF_AZIMUTH_DEG
            surface_tilt = np.abs(rotation)
            surface_azimuth = np.where(rotation >= 0, 270.0, 90.0)
            gap[i] = pitch - width
        elif layout.kind is Kind.VERTICAL:
            rotation = surface_tilt = 90.0
            ref_azimuth = surface_azimuth = layout.azimuth_deg
            mask = farmed_mask(pitch, layout.unfarmed_strip_m)
            gap[i] = pitch
        else:
            rotation = surface_tilt = layout.tilt_deg
            ref_azimuth = surface_azimuth = layout.azimuth_deg
            gap[i] = pitch - width * math.cos(math.radians(layout.tilt_deg))
        energy[i] = _monthly_energy(
            weather, surface_tilt, surface_azimuth, gcr, height, pitch, layout.module, losses
        )
        light[i], darkest[i] = ground_light(weather, rotation, ref_azimuth, gcr, height, width, mask)

    table = PhysicsTable(energy, light, reference_energy_kwh_per_acre(weather, layout.module, losses))
    darkest.setflags(write=False)
    gap.setflags(write=False)
    return PhysicsResult(table, darkest, gap)
