"""Light on the front and back of the panels, and the loss to reflection (design spec §5.3).

`panel_irradiance` is the infinite-rows model of pvlib-python 0.16.1 (`pvlib/bifacial/infinite_sheds.py`,
with the Hay-Davies sky model from `pvlib/irradiance.py`); `iam_beam` and `iam_diffuse` are the Martin-Ruiz
reflection models from `pvlib/iam.py`. Adapted for numpy only (BSD 3-Clause; see NOTICE).
"""

import numpy as np

from apv_physics import viewfactors as vf
from apv_physics.viewfactors import cosd, sind

_TILT_GRID_STEP = 0.5  # degrees; view factors for trackers are tabulated on this grid and interpolated


def iam_beam(aoi_deg, a_r: float = 0.16) -> np.ndarray:
    """Share of direct light that gets through the glass at angle of incidence `aoi_deg` (Martin-Ruiz)."""
    aoi = np.asarray(aoi_deg, dtype=float)
    iam = (1 - np.exp(-cosd(aoi) / a_r)) / (1 - np.exp(-1 / a_r))
    return np.where(np.abs(aoi) >= 90.0, 0.0, iam)


def iam_diffuse(surface_tilt_deg, a_r: float = 0.16) -> tuple[np.ndarray, np.ndarray]:
    """Share of sky light and of ground-reflected light that gets through the glass (Martin-Ruiz).

    Returns (sky, ground) for a surface tilted `surface_tilt_deg` from horizontal (above 90 faces down).
    """
    c1, c2 = 0.4244, 0.5 * a_r - 0.154
    tilt = np.asarray(surface_tilt_deg, dtype=float)
    # exactly flat or face-down makes the formula 0 / 0; pvlib nudges 0 and 180 only, which leaves a NaN for
    # tilts a hair away from them, so the nudge here covers the whole neighbourhood
    tilt = np.clip(tilt, 1e-6, 180 - 1e-6)
    beta = np.radians(tilt)
    sin_beta = np.where(tilt < 90, np.sin(beta), np.sin(np.pi - beta))
    term_sky = sin_beta + (np.pi - beta - sin_beta) / (1 + np.cos(beta))
    term_gnd = sin_beta + (beta - sin_beta) / (1 - np.cos(beta))
    iam_sky = 1 - np.exp(-(c1 + c2 * term_sky) * term_sky / a_r)
    iam_gnd = 1 - np.exp(-(c1 + c2 * term_gnd) * term_gnd / a_r)
    return iam_sky, iam_gnd


def _aoi_projection(surface_tilt, surface_azimuth, zenith, azimuth):
    projection = cosd(surface_tilt) * cosd(zenith) + sind(surface_tilt) * sind(zenith) * cosd(
        azimuth - surface_azimuth
    )
    return np.clip(projection, -1, 1)


def _view_factors(surface_tilt, gcr: float, height: float, pitch: float, max_rows: float):
    """Row-to-sky, row-to-ground and ground-to-sky view factors for a scalar tilt or an hourly array of tilts."""

    def compute(tilt):
        return (
            vf.vf_row_sky_2d_integ(tilt, gcr, 0.0, 1.0),
            vf.vf_row_ground_2d_integ(tilt, gcr, x0=0.0, x1=1.0, g0=0.0, g1=1.0),
            vf.vf_ground_sky_2d_integ(tilt, gcr, height, pitch, max_rows=max_rows, g0=0, g1=1),
        )

    if np.ndim(surface_tilt) == 0:
        return compute(float(surface_tilt))
    lo = np.floor(surface_tilt.min() / _TILT_GRID_STEP) * _TILT_GRID_STEP
    hi = np.ceil(surface_tilt.max() / _TILT_GRID_STEP) * _TILT_GRID_STEP
    grid = np.arange(lo, hi + 1.5 * _TILT_GRID_STEP, _TILT_GRID_STEP)
    return tuple(np.interp(surface_tilt, grid, table) for table in compute(grid))


def _one_side(surface_tilt, surface_azimuth, zenith, azimuth, gcr, height, pitch, ghi, dhi, dni, albedo):
    """Direct, sky and ground-reflected light on one face of the rows (pvlib `get_irradiance_poa`)."""
    max_rows = np.ceil(height / (pitch * vf.tand(5)))
    tan_phi = vf.solar_projection_tangent(zenith, azimuth, surface_azimuth)
    phi = np.degrees(np.arctan(tan_phi))
    f_gnd_beam = vf.unshaded_ground_fraction(surface_tilt, phi, gcr)
    vf_row_sky, vf_row_gnd, vf_gnd_sky = _view_factors(surface_tilt, gcr, height, pitch, max_rows)

    projection = _aoi_projection(surface_tilt, surface_azimuth, zenith, azimuth)
    aoi = np.degrees(np.arccos(projection))
    # share of the row width shaded by the row in front
    with np.errstate(divide="ignore", invalid="ignore"):
        x = gcr * (sind(surface_tilt) * tan_phi + cosd(surface_tilt))
        f_x = 1 - 1.0 / x
    f_x = np.where(aoi < 90, f_x, 1.0)
    f_x = np.where(x > 1.0, f_x, 0.0)

    sky = dhi * vf_row_sky
    ground = albedo * (f_gnd_beam * (ghi - dhi) + vf_gnd_sky * dhi) * vf_row_gnd
    direct = np.maximum(dni * projection, 0) * (1 - f_x)
    clean = [
        np.maximum(np.nan_to_num(v, nan=0.0, posinf=0.0, neginf=0.0), 0.0) for v in (direct, sky, ground)
    ]
    return (*clean, aoi)


def panel_irradiance(
    surface_tilt, surface_azimuth, zenith, azimuth, gcr: float, height: float, pitch: float,
    ghi, dhi, dni, dni_extra, albedo: float,
) -> dict[str, np.ndarray]:  # fmt: skip
    """Light on the front and back of the rows, in W/m2 before reflection loss.

    `surface_tilt` and `surface_azimuth` are scalars (fixed rows) or hourly arrays (trackers). `height` is the
    row centre height. Keys: front_direct, front_sky, front_ground, back_direct, back_sky, back_ground,
    aoi_front, aoi_back.
    """
    zenith, azimuth = np.asarray(zenith, dtype=float), np.asarray(azimuth, dtype=float)
    ghi, dhi, dni = (np.asarray(v, dtype=float) for v in (ghi, dhi, dni))
    if np.ndim(surface_tilt) > 0:
        surface_tilt = np.asarray(surface_tilt, dtype=float)
        surface_azimuth = np.asarray(surface_azimuth, dtype=float)

    # Hay-Davies: the part of the sky light that comes from near the sun is handled as direct light
    anisotropy = dni / np.asarray(dni_extra, dtype=float)
    cos_zenith = np.maximum(cosd(zenith), 0.01745)
    circumsolar_horizontal = np.maximum(dhi * anisotropy * np.maximum(cosd(zenith), 0) / cos_zenith, 0)
    circumsolar_normal = np.maximum(dhi * anisotropy / cos_zenith, 0)
    dhi_iso = dhi - circumsolar_horizontal
    dni_all = dni + circumsolar_normal

    args = (zenith, azimuth, gcr, height, pitch, ghi, dhi_iso, dni_all, albedo)
    front = _one_side(surface_tilt, surface_azimuth, *args)
    back = _one_side(180.0 - surface_tilt, (180.0 + surface_azimuth) % 360.0, *args)
    return {
        "front_direct": front[0],
        "front_sky": front[1],
        "front_ground": front[2],
        "back_direct": back[0],
        "back_sky": back[1],
        "back_ground": back[2],
        "aoi_front": front[3],
        "aoi_back": back[3],
    }


def effective_irradiance(
    parts: dict[str, np.ndarray], surface_tilt, bifaciality: float, rear_shading: float, a_r: float = 0.16
) -> np.ndarray:
    """Light the cells can use: front plus the back's share, each after reflection loss (W/m2)."""
    tilt = np.asarray(surface_tilt, dtype=float)
    front_sky, front_gnd = iam_diffuse(tilt, a_r)
    back_sky, back_gnd = iam_diffuse(180.0 - tilt, a_r)
    front = (
        parts["front_direct"] * iam_beam(parts["aoi_front"], a_r)
        + parts["front_sky"] * front_sky
        + parts["front_ground"] * front_gnd
    )
    back = (
        parts["back_direct"] * iam_beam(parts["aoi_back"], a_r)
        + parts["back_sky"] * back_sky
        + parts["back_ground"] * back_gnd
    )
    return front + bifaciality * (1 - rear_shading) * back
