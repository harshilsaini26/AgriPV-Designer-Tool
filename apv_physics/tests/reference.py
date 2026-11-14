"""The engine's calculation chain rebuilt from pvlib calls only. Test-only: the reference for design spec §7, V1."""

import numpy as np
import pvlib
from pvlib.bifacial import infinite_sheds
from pvlib.bifacial import utils as pv

from apv_physics import Kind, Layout, Losses, Weather


def _surface(weather: Weather, layout: Layout, gcr: float):
    """Surface tilt and azimuth: scalars for fixed and vertical rows, hourly arrays for trackers."""
    if layout.kind is Kind.TRACKER:
        tr = pvlib.tracking.singleaxis(
            weather.zenith, weather.azimuth, axis_tilt=0, axis_azimuth=180,
            max_angle=layout.max_angle_deg, backtrack=True, gcr=gcr,
        )  # fmt: skip
        return np.nan_to_num(tr["surface_tilt"]), np.nan_to_num(tr["surface_azimuth"], nan=90.0)
    return (90.0 if layout.kind is Kind.VERTICAL else layout.tilt_deg), layout.azimuth_deg


def pvlib_reference(
    weather: Weather, layout: Layout, gcr: float, losses: Losses
) -> tuple[np.ndarray, np.ndarray]:
    """Monthly kWh per kWp and monthly ground light fraction on the farmed band, both shape (12,)."""
    w = weather
    pitch, height = layout.collector_width_m / gcr, layout.center_height_m
    tilt, azimuth = _surface(w, layout, gcr)

    # energy
    aoi = pvlib.irradiance.aoi(tilt, azimuth, w.zenith, w.azimuth)
    out = infinite_sheds.get_irradiance(
        tilt, azimuth, w.zenith, w.azimuth, gcr, height, pitch, w.ghi, w.dhi, w.dni,
        albedo=losses.albedo, model="haydavies", dni_extra=w.dni_extra,
        iam_front=pvlib.iam.martin_ruiz(aoi), iam_back=pvlib.iam.martin_ruiz(180.0 - aoi),
    )  # fmt: skip
    front_iam = pvlib.iam.martin_ruiz_diffuse(tilt)
    back_iam = pvlib.iam.martin_ruiz_diffuse(180.0 - np.asarray(tilt))
    nz = np.nan_to_num
    front = (
        nz(out["poa_front_direct"])
        + nz(out["poa_front_sky_diffuse"]) * front_iam["sky"]
        + nz(out["poa_front_ground_diffuse"]) * front_iam["ground"]
    )
    back = (
        nz(out["poa_back_direct"])
        + nz(out["poa_back_sky_diffuse"]) * back_iam["sky"]
        + nz(out["poa_back_ground_diffuse"]) * back_iam["ground"]
    )
    g_eff = front + layout.module.bifaciality * (1 - losses.rear_shading) * back
    temp_cell = pvlib.temperature.faiman(g_eff, w.temp_air, w.wind_speed)
    dc = np.clip(pvlib.pvsystem.pvwatts_dc(g_eff, temp_cell, 1000.0, layout.module.temp_coeff_per_c), 0, None)
    pac0 = 1000.0 / losses.dc_ac_ratio
    ac = pvlib.inverter.pvwatts(
        dc * losses.dc_factor, pac0 / losses.inverter_efficiency, eta_inv_nom=losses.inverter_efficiency
    )
    energy = np.bincount(w.month - 1, weights=nz(ac) * losses.ac_factor, minlength=12) / 1000.0

    # ground light on the farmed band
    strip = layout.unfarmed_strip_m if layout.kind is Kind.VERTICAL else 0.0
    g0, g1 = strip / 2 / pitch, 1 - strip / 2 / pitch
    anisotropy = np.clip(w.dni / w.dni_extra, 0, 1)
    beam = w.dni * np.clip(np.cos(np.radians(w.zenith)), 0, None) + w.dhi * anisotropy
    iso = w.dhi * (1 - anisotropy)
    phi = np.degrees(np.arctan(pv._solar_projection_tangent(w.zenith, w.azimuth, azimuth)))
    max_rows = np.ceil(height / (pitch * np.tan(np.radians(5))))
    unshaded = pv._unshaded_ground_fraction(
        tilt, phi, gcr, height=height, pitch=pitch, max_rows=50, max_zenith=90, g0=g0, g1=g1
    )
    sky_view = pv.vf_ground_sky_2d_integ(tilt, gcr, height, pitch, max_rows=max_rows, g0=g0, g1=g1)
    lit = beam * unshaded + iso * sky_view
    light = np.bincount(w.month - 1, weights=lit, minlength=12) / np.bincount(
        w.month - 1, weights=beam + iso, minlength=12
    )
    return energy, light
