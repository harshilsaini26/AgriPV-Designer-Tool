"""2-D view factors for rows of panels that repeat without end over flat ground.

Adapted from pvlib-python 0.16.1, `pvlib/bifacial/utils.py` (BSD 3-Clause; see NOTICE). The algorithms are
unchanged; pandas handling and deprecated parameters were removed so the module needs numpy only.

Conventions: angles in degrees; `gcr` is row width / row pitch; `height` is the height of the row centre and
is in the same unit as `pitch`; ground positions are fractions of the pitch measured from under a row centre.
"""

import numpy as np


def sind(angle):
    return np.sin(np.radians(angle))


def cosd(angle):
    return np.cos(np.radians(angle))


def tand(angle):
    return np.tan(np.radians(angle))


def solar_projection_tangent(solar_zenith, solar_azimuth, surface_azimuth):
    """Tangent of the sun's zenith angle projected onto the plane across the rows."""
    rotation = solar_azimuth - surface_azimuth
    return cosd(rotation) * tand(solar_zenith)


def unshaded_ground_fraction(
    tracker_rotation, phi, gcr, height=None, pitch=None, max_rows=10, max_zenith=85, g0=0, g1=1
):
    """Share of the ground segment (g0, g1) that is in direct sun, for projected sun zenith `phi`."""
    if np.isscalar(g0) and g0 == 0 and np.isscalar(g1) and g1 == 1:
        height = 1
        pitch = 1 / gcr
    squeeze = []
    if np.isscalar(g0) and np.isscalar(g1):
        squeeze.append(0)
    if np.isscalar(tracker_rotation) and np.isscalar(phi):
        squeeze.append(1)
    tracker_rotation = np.atleast_1d(tracker_rotation)[np.newaxis, np.newaxis, :]
    phi = np.atleast_1d(phi)[np.newaxis, np.newaxis, :]
    g0 = np.atleast_1d(g0)[np.newaxis, :, np.newaxis]
    g1 = np.atleast_1d(g1)[np.newaxis, :, np.newaxis]
    k = np.arange(-max_rows, max_rows + 2)[:, np.newaxis, np.newaxis]
    collector_width = pitch * gcr
    l_cos = collector_width * cosd(tracker_rotation)
    l_sin = collector_width * sind(tracker_rotation)
    tanphi = tand(phi)
    # the two edges of each row, then where their shadows fall on the ground
    c = (k * pitch + 0.5 * l_cos, height + 0.5 * l_sin)
    d = (k * pitch - 0.5 * l_cos, height - 0.5 * l_sin)
    cp = c[0] + c[1] * tanphi
    dp = d[0] + d[1] * tanphi
    swap = dp > cp
    cp, dp = np.where(swap, dp, cp), np.where(swap, cp, dp)
    a = g0 * pitch
    b = g1 * pitch
    fs = np.full_like(cp, 1.0)
    fs = np.where((dp <= a) & (a <= cp) & (cp < b), (cp - a) / (b - a), fs)
    fs = np.where((dp < a) & (cp < a), 0.0, fs)
    fs = np.where((a < dp) & (dp <= b) & (cp >= b), (b - dp) / (b - a), fs)
    fs = np.where((a < dp) & (dp < b) & (a < cp) & (cp < b), (cp - dp) / (b - a), fs)
    fs = np.where((dp > b) & (cp > b), 0.0, fs)
    f_gnd_beam = 1 - np.clip(np.sum(fs, axis=0), 0, 1)  # sum over rows
    phi = phi[0, :, :]
    f_gnd_beam = np.where(np.abs(phi) > max_zenith, 0.0, f_gnd_beam)
    return f_gnd_beam.squeeze(axis=tuple(squeeze))


def vf_ground_sky_2d(rotation, gcr, x, pitch, height, max_rows=10):
    """Share of the sky dome seen from ground positions `x`. Returns shape (len(x), len(rotation))."""
    x = np.atleast_1d(x)[:, np.newaxis, np.newaxis]
    rotation = np.atleast_1d(rotation)[np.newaxis, :, np.newaxis]
    all_k = np.arange(-max_rows, max_rows + 2)
    width = gcr * pitch / 2.0
    distance_to_row_centers = (all_k - x) * pitch
    dy = width * sind(rotation)
    dx = width * cosd(rotation)
    # angles from x to the two edges of each row
    edge_1 = np.arctan2(height + dy, distance_to_row_centers + dx)
    edge_2 = np.arctan2(height - dy, distance_to_row_centers - dx)
    lesser, greater = np.minimum(edge_1, edge_2), np.maximum(edge_1, edge_2)
    # sky seen through each gap: between one row's far edge and the next row's near edge
    gaps = np.clip(np.cos(greater[:, :, 1:]) - np.cos(lesser[:, :, :-1]), a_min=0.0, a_max=None)
    return np.sum(gaps, axis=-1) / 2


def vf_ground_sky_2d_integ(tracker_rotation, gcr, height, pitch, max_rows=10, g0=0, g1=1):
    """Average share of the sky dome seen from the ground segment (g0, g1)."""
    squeeze = []
    if np.isscalar(g0) and np.isscalar(g1):
        squeeze.append(0)
    if np.isscalar(tracker_rotation):
        squeeze.append(1)
    tracker_rotation = np.atleast_1d(tracker_rotation)[np.newaxis, np.newaxis, :]
    g0 = np.atleast_1d(g0)[np.newaxis, :, np.newaxis]
    g1 = np.atleast_1d(g1)[np.newaxis, :, np.newaxis]
    k = np.arange(-max_rows, max_rows + 1)[:, np.newaxis, np.newaxis]
    collector_width = pitch * gcr
    l_cos = collector_width * cosd(tracker_rotation)
    l_sin = collector_width * sind(tracker_rotation)
    a = (g0 * pitch, 0)
    b = (g1 * pitch, 0)
    # the sky "slat" between two adjacent rows
    sign = np.sign(tracker_rotation)
    c = ((k + 1) * pitch + sign * 0.5 * l_cos, height + sign * 0.5 * l_sin)
    d = (c[0] - pitch, c[1])
    # the row edges that can block the view from each end of the ground segment
    left = (k * pitch - 0.5 * l_cos, height - 0.5 * l_sin)
    right = (k * pitch + 0.5 * l_cos, height + 0.5 * l_sin)
    angle_left = _angle(a, left)
    angle_right = _angle(a, right)
    ob_left = (
        np.where(angle_left > angle_right, right[0], left[0]),
        np.where(angle_left > angle_right, right[1], left[1]),
    )
    left = (left[0] + pitch, left[1])
    right = (right[0] + pitch, right[1])
    angle_left = _angle(b, left)
    angle_right = _angle(b, right)
    ob_right = (
        np.where(angle_left > angle_right, left[0], right[0]),
        np.where(angle_left > angle_right, left[1], right[1]),
    )
    ac, ad, bc, bd = _obstructed_string_lengths(a, b, c, d, ob_left, ob_right)
    vf_slats = 0.5 * (1 / ((g1 - g0) * pitch)) * ((ac + bd) - (bc + ad))
    vf_total = np.sum(np.maximum(vf_slats, 0), axis=0)  # sum over rows
    return vf_total.squeeze(axis=tuple(squeeze))


def _vf_poly(surface_tilt, gcr, x, delta):
    """A term common to the row view factors."""
    a = 1 / gcr
    c = cosd(surface_tilt)
    return np.sqrt(a * a + 2 * delta * a * c * x + x * x)


def vf_row_sky_2d(surface_tilt, gcr, x):
    """Share of the sky dome seen from point `x` on the row surface (x = 0 at the lower edge)."""
    p = _vf_poly(surface_tilt, gcr, 1 - x, -1)
    return 0.5 * (1 + (1 / gcr * cosd(surface_tilt) - (1 - x)) / p)


def vf_row_sky_2d_integ(surface_tilt, gcr, x0=0, x1=1):
    """Average share of the sky dome seen from the row surface between x0 and x1."""
    squeeze = []
    if np.isscalar(x0) and np.isscalar(x1):
        squeeze.append(0)
    if np.isscalar(surface_tilt):
        squeeze.append(1)
    surface_tilt = np.atleast_1d(surface_tilt)[np.newaxis, :]
    x0 = np.atleast_1d(x0)[:, np.newaxis]
    x1 = np.atleast_1d(x1)[:, np.newaxis]
    swap = surface_tilt < 0
    x0, x1 = np.where(swap, 1 - x1, x0), np.where(swap, 1 - x0, x1)
    u = np.abs(x1 - x0)
    p0 = _vf_poly(surface_tilt, gcr, 1 - x0, -1)
    p1 = _vf_poly(surface_tilt, gcr, 1 - x1, -1)
    with np.errstate(divide="ignore"):
        result = np.where(u < 1e-6, vf_row_sky_2d(surface_tilt, gcr, x0), 0.5 * (1 + 1 / u * (p1 - p0)))
    return result.squeeze(axis=tuple(squeeze))


def vf_row_ground_2d_integ(surface_tilt, gcr, height=None, pitch=None, x0=0, x1=1, max_rows=20, g0=0, g1=1):
    """View factor from the row surface segment (x0, x1) to the ground segment (g0, g1)."""
    if all(np.isscalar(v) for v in [x0, x1, g0, g1]) and (g0 == 0 and g1 == 1 and x0 == 0 and x1 == 1):
        height = 1
        pitch = 1 / gcr
    squeeze = []
    if np.isscalar(g0) and np.isscalar(g1):
        squeeze.append(0)
    if np.isscalar(x0) and np.isscalar(x1):
        squeeze.append(1)
    if np.isscalar(surface_tilt):
        squeeze.append(2)
    surface_tilt = np.where(surface_tilt == 180, 179.9999, surface_tilt)
    surface_tilt = np.where(surface_tilt == -180, -179.9999, surface_tilt)
    surface_tilt = np.atleast_1d(surface_tilt)[np.newaxis, np.newaxis, np.newaxis, :]
    x0 = np.atleast_1d(x0)[np.newaxis, np.newaxis, :, np.newaxis]
    x1 = np.atleast_1d(x1)[np.newaxis, np.newaxis, :, np.newaxis]
    g0 = np.atleast_1d(g0)[np.newaxis, :, np.newaxis, np.newaxis]
    g1 = np.atleast_1d(g1)[np.newaxis, :, np.newaxis, np.newaxis]
    k = np.arange(-max_rows, max_rows)[:, np.newaxis, np.newaxis, np.newaxis]
    collector_width = pitch * gcr
    l_cos = collector_width * cosd(surface_tilt)
    l_sin = collector_width * sind(surface_tilt)
    # the lower edges of the neighbouring rows block part of the view to the ground
    ob_right = (-pitch - 0.5001 * l_cos, height - 0.5001 * abs(l_sin))
    ob_left = (ob_right[0] + pitch, ob_right[1])
    invert = surface_tilt < 0
    temp = ob_right[0]
    ob_right = (np.where(invert, -ob_left[0], ob_right[0]), ob_right[1])
    ob_left = (np.where(invert, -temp, ob_left[0]), ob_left[1])
    a = ((x0 - 0.5) * l_cos, height + (x0 - 0.5) * l_sin)
    b = ((x1 - 0.5) * l_cos, height + (x1 - 0.5) * l_sin)
    c = ((k + g0) * pitch, 0)
    d = ((k + g1) * pitch, 0)
    ac, ad, bc, bd = _obstructed_string_lengths(a, b, c, d, ob_left, ob_right)
    vf_slats = 1 / (2 * (x1 - x0) * collector_width) * ((ac + bd) - (bc + ad))
    vf_total = np.sum(np.maximum(vf_slats, 0), axis=0)  # sum over ground segments
    return vf_total.squeeze(axis=tuple(squeeze))


def _obstructed_string_lengths(a, b, c, d, ob_left, ob_right):
    """Lengths of the four strings a-c, a-d, b-c, b-d, each bent round an obstruction where one is in the way."""
    ang_a_left, ang_a_right = _angle(a, ob_left), _angle(a, ob_right)
    ang_b_left, ang_b_right = _angle(b, ob_left), _angle(b, ob_right)

    def string(p, q, ang_left, ang_right):
        ang = _angle(p, q)
        length = np.where(ang - ang_left > 1e-8, _dist(p, ob_left) + _dist(ob_left, q), _dist(p, q))
        return np.where(ang_right - ang > 1e-8, _dist(p, ob_right) + _dist(ob_right, q), length)

    ac = string(a, c, ang_a_left, ang_a_right)
    ad = string(a, d, ang_a_left, ang_a_right)
    bc = string(b, c, ang_b_left, ang_b_right)
    bd = string(b, d, ang_b_left, ang_b_right)
    return ac, ad, bc, bd


def _dist(p1, p2):
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5


def _angle(p1, p2):
    return np.arctan2(p2[1] - p1[1], p2[0] - p1[0])
