"""Light reaching the ground between the rows, strip by strip (design spec §5.4).

The model is a cross-section across rows that repeat without end. A horizontal axis `x` runs across the rows,
pointing away from `ref_azimuth_deg`. Row k is centred at x = k * pitch, at height `height`; its two edges are
at (k * pitch +/- w/2 * cos(rotation), height +/- w/2 * sin(rotation)), where a positive `rotation` means the
panel faces `ref_azimuth_deg`. A point at (x, z) casts its shadow at x + z * tan(phi), where phi is the sun's
zenith angle projected onto the cross-section. The ground under one pitch is split into N_STRIPS strips;
strip j covers [j, j + 1) * pitch / N_STRIPS.
"""

import math

import numpy as np

from apv_physics import viewfactors as vf
from apv_physics.inputs import Weather
from apv_physics.viewfactors import cosd, sind

N_STRIPS = 100
_ROTATION_GRID_STEP = 1.0  # degrees; sky view for trackers is tabulated on this grid (spec §5.4)
_MAX_TAN_PHI = 1e9  # sun on the horizon across the rows: the shadow covers everything anyway


def strip_unshaded(rotation, tan_phi, gcr: float, height: float, pitch: float) -> np.ndarray:
    """Share of each ground strip in direct sun, shape (n_hours, N_STRIPS).

    The shadow of one row is the stretch of ground between the shadows of its two edges. It repeats every
    pitch, so the overlap with each strip is exact and the mean over strips is 1 - shadow length / pitch.
    """
    tan_phi = np.clip(np.atleast_1d(np.asarray(tan_phi, dtype=float)), -_MAX_TAN_PHI, _MAX_TAN_PHI)
    rotation, tan_phi = np.broadcast_arrays(np.atleast_1d(np.asarray(rotation, dtype=float)), tan_phi)
    half_cos = 0.5 * gcr * pitch * cosd(rotation)
    half_sin = 0.5 * gcr * pitch * sind(rotation)
    edge_a = half_cos + (height + half_sin) * tan_phi
    edge_b = -half_cos + (height - half_sin) * tan_phi
    length = np.minimum(np.abs(edge_a - edge_b), pitch)[:, np.newaxis]
    start = np.mod(np.minimum(edge_a, edge_b), pitch)[:, np.newaxis]

    strip_width = pitch / N_STRIPS
    strip_start = np.arange(N_STRIPS) * strip_width
    strip_end = strip_start + strip_width
    shaded = np.zeros((rotation.size, N_STRIPS))
    for shift in (0.0, -pitch):  # the shadow itself, and the part that wraps round from the row behind
        lo = start + shift
        shaded += np.clip(np.minimum(lo + length, strip_end) - np.maximum(lo, strip_start), 0.0, None)
    return 1.0 - np.clip(shaded / strip_width, 0.0, 1.0)


def strip_sky_view(rotation, gcr: float, height: float, pitch: float) -> np.ndarray:
    """Share of the sky dome seen from the centre of each strip.

    A scalar `rotation` gives shape (N_STRIPS,). An hourly array (trackers) gives shape (n_hours, N_STRIPS),
    interpolated from a table on a 1 degree grid of rotation. The table covers one turning direction only: a
    row turned the other way is the mirror image, so its strips are read in reverse order.
    """
    x = (np.arange(N_STRIPS) + 0.5) / N_STRIPS
    max_rows = np.ceil(height / (pitch * vf.tand(5)))
    if np.ndim(rotation) == 0:
        return vf.vf_ground_sky_2d(float(rotation), gcr, x, pitch, height, max_rows=max_rows)[:, 0]
    rotation = np.asarray(rotation, dtype=float)
    turn = np.abs(rotation) / _ROTATION_GRID_STEP
    grid = np.arange(0.0, np.ceil(turn.max()) + 1.5) * _ROTATION_GRID_STEP
    table = vf.vf_ground_sky_2d(grid, gcr, x, pitch, height, max_rows=max_rows).T  # (len(grid), N_STRIPS)
    below = np.minimum(np.floor(turn).astype(int), len(grid) - 2)
    weight = (turn - below)[:, np.newaxis]
    view = table[below] * (1.0 - weight) + table[below + 1] * weight
    return np.where((rotation < 0)[:, np.newaxis], view[:, ::-1], view)


def farmed_mask(pitch: float, unfarmed_strip_m: float) -> np.ndarray:
    """Which strips are cropped: those farther than half the unfarmed strip from the nearest row centre."""
    centre = (np.arange(N_STRIPS) + 0.5) / N_STRIPS * pitch
    distance = np.minimum(centre, pitch - centre)
    mask = distance > unfarmed_strip_m / 2 if unfarmed_strip_m > 0 else np.ones(N_STRIPS, dtype=bool)
    if not mask.any():
        raise ValueError(
            f"unfarmed_strip_m leaves no farmed ground: a {unfarmed_strip_m} m strip under each row covers "
            f"the whole {pitch:.2f} m row pitch"
        )
    return mask


def ground_light(
    weather: Weather,
    rotation,
    ref_azimuth_deg: float,
    gcr: float,
    height: float,
    collector_width_m: float,
    mask: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Monthly light on the farmed ground as a share of open-field light.

    Returns (light_mean, light_darkest_tenth), each of shape (12,) and within [0, 1]. The second is the same
    ratio over the tenth of farmed strips that got the least light in that month. A month with no hours
    gives 1.0.
    """
    pitch = collector_width_m / gcr
    anisotropy = np.clip(weather.dni / weather.dni_extra, 0.0, 1.0)
    # direct light, with the part of the sky light that comes from near the sun; the rest is even sky light
    beam = weather.dni * np.maximum(cosd(weather.zenith), 0.0) + weather.dhi * anisotropy
    iso = weather.dhi * (1.0 - anisotropy)
    tan_phi = vf.solar_projection_tangent(weather.zenith, weather.azimuth, ref_azimuth_deg)
    light = beam[:, np.newaxis] * strip_unshaded(rotation, tan_phi, gcr, height, pitch)
    light += iso[:, np.newaxis] * strip_sky_view(rotation, gcr, height, pitch)
    open_field = beam + iso

    n_dark = math.ceil(0.1 * int(mask.sum()))
    mean, darkest = np.ones(12), np.ones(12)
    for m in range(1, 13):
        hours = weather.month == m
        total = open_field[hours].sum()
        if total <= 0:
            continue
        strips = light[hours].sum(axis=0)[mask]
        mean[m - 1] = strips.mean() / total
        darkest[m - 1] = np.sort(strips)[:n_dark].mean() / total
    return np.clip(mean, 0.0, 1.0), np.clip(darkest, 0.0, 1.0)
