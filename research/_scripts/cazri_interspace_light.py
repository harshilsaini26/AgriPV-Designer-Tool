"""Season-mean light fraction on the cropped interspaces of the ICAR-CAZRI Jodhpur agrivoltaic plant.

Usage: python -I cazri_interspace_light.py [lower_edge_height_m] [module_length_along_slope_m]

Why: Poonia & Santra (2024) report crop yields in the interspaces, but light only as midday PAR in the *shaded*
part. The AgriPV Lab model needs the season-mean light over the whole cropped area relative to open field (L_s),
so this script models it from the published layout.

Layout (Poonia & Santra 2024, "PV Module Installation"): rows run east-west, modules tilted 26° to the south,
module 0.992 x 1.640 m; arrays one, two or three modules deep with clear inter-row gaps of 3.2, 6.4 and 9.6 m.
Two-row array (AVS-3): bottom row 100% PV density, top row 60%. Three-row arrays: AVS-4 (100/100/60) and AVS-5
(100/60/60). A 60% row is treated as 40% transparent.
Not published, so assumed (and varied in the sensitivity runs): the lower-edge height (default 0.75 m) and that
modules are mounted portrait (1.64 m up the slope).

Method: 2-D cross-section (rows long east-west), periodic arrays. Hourly sun positions for Jodhpur (26.25 N,
73.02 E) over each season; clear-sky global irradiance (Haurwitz) split into beam and isotropic diffuse with a
monthly diffuse fraction (monsoon months cloudier). Beam reaches a ground point unless the ray to the sun crosses
an array; diffuse is the cosine-weighted share of sky the point can see. Ground reflection is ignored.
Prints the light fraction (season irradiation on the interspace / open field) per design and season.
"""

import math
import sys

LAT = math.radians(26.25)
TILT = math.radians(26)
DIFFUSE_FRACTION = {1: 0.25, 2: 0.25, 3: 0.3, 4: 0.3, 5: 0.35, 6: 0.45, 7: 0.55, 8: 0.55, 9: 0.45, 10: 0.3,
                    11: 0.25, 12: 0.25}  # fmt: skip
SEASONS = {
    "kharif (Jul-Sep, moong / guar)": (182, 273),
    "rabi (Nov-Feb, chickpea / cumin)": (305, 424),  # day 305 to 59 of the next year
}
DESIGNS = {  # name: (inter-row gap m, densities of the module rows from bottom to top)
    "2-row (AVS-3)": (6.4, [1.0, 0.6]),
    "3-row (AVS-4)": (9.6, [1.0, 1.0, 0.6]),
    "3-row (AVS-5)": (9.6, [1.0, 0.6, 0.6]),
    "1-row (AVS-1)": (3.2, [1.0]),
}
DAY_MONTH = [(31, 1), (59, 2), (90, 3), (120, 4), (151, 5), (181, 6), (212, 7), (243, 8), (273, 9), (304, 10),
             (334, 11), (365, 12)]  # fmt: skip


def month_of(doy: int) -> int:
    return next(m for end, m in DAY_MONTH if (doy - 1) % 365 + 1 <= end)


def sun(doy: int, hour: float) -> tuple[float, float] | None:
    """(elevation, signed north component of the unit sun vector) or None below the horizon. Solar time."""
    decl = math.radians(23.45) * math.sin(2 * math.pi * (284 + doy) / 365)
    ha = math.radians(15 * (hour - 12))
    sin_e = math.sin(LAT) * math.sin(decl) + math.cos(LAT) * math.cos(decl) * math.cos(ha)
    if sin_e <= 0.02:
        return None
    e = math.asin(sin_e)
    # north component of the sun direction: cos(e) * cos(azimuth from north)
    north = (math.sin(decl) - math.sin(LAT) * sin_e) / math.cos(LAT)
    return e, north


def segments(gap: float, dens: list[float], h0: float, mod_len: float):
    """Panel segments (y1, z1, y2, z2, transmittance) in one period, y north. Returns segments, pitch, strip."""
    segs, y, z = [], 0.0, h0
    for d in dens:
        y2, z2 = y + mod_len * math.cos(TILT), z + mod_len * math.sin(TILT)
        segs.append((y, z, y2, z2, 1 - d))
        y, z = y2, z2
    depth = y
    return segs, depth + gap, (depth, depth + gap)


def transmit(y0: float, dy: float, dz: float, segs, pitch: float) -> float:
    """Fraction of a ray from ground point (y0, 0) along (dy, dz) that passes all panels."""
    t_total = 1.0
    for k in range(-6, 7):
        for y1, z1, y2, z2, tr in segs:
            y1k, y2k = y1 + k * pitch, y2 + k * pitch
            # solve y0 + s*dy = y1k + u*(y2k - y1k), s*dz = z1 + u*(z2 - z1), s > 0, 0 <= u <= 1
            a11, a12, a21, a22 = dy, -(y2k - y1k), dz, -(z2 - z1)
            det = a11 * a22 - a12 * a21
            if abs(det) < 1e-12:
                continue
            b1, b2 = y1k - y0, z1
            s = (b1 * a22 - a12 * b2) / det
            u = (a11 * b2 - a21 * b1) / det
            if s > 0 and 0 <= u <= 1:
                t_total *= tr
    return t_total


def sky_view(y0: float, segs, pitch: float, n: int = 180) -> float:
    """Cosine-weighted visible sky fraction (2-D, isotropic)."""
    tot = vis = 0.0
    for i in range(n):
        th = -math.pi / 2 + (i + 0.5) * math.pi / n  # angle from vertical in the N-S plane
        w = math.cos(th)
        tot += w
        vis += w * transmit(y0, math.sin(th), math.cos(th), segs, pitch)
    return vis / tot


def light_fraction(design: str, season: tuple[int, int], h0: float, mod_len: float, npts: int = 25) -> float:
    gap, dens = DESIGNS[design]
    segs, pitch, (ya, yb) = segments(gap, dens, h0, mod_len)
    pts = [ya + (i + 0.5) * (yb - ya) / npts for i in range(npts)]
    svf = [sky_view(y, segs, pitch) for y in pts]
    got = full = 0.0
    for doy in range(season[0], season[1] + 1, 3):
        fd = DIFFUSE_FRACTION[month_of(doy)]
        d = (doy - 1) % 365 + 1
        for h10 in range(50, 190, 5):  # 05:00-18:30 solar time, half-hour steps
            s = sun(d, h10 / 10)
            if s is None:
                continue
            e, north = s
            ghi = 1098 * math.sin(e) * math.exp(-0.057 / math.sin(e))
            beam, diff = (1 - fd) * ghi, fd * ghi
            # ray toward the sun in the N-S plane: horizontal north component and vertical component
            dy, dz = north, math.sin(e)
            for y, sv in zip(pts, svf):
                got += beam * transmit(y, dy, dz, segs, pitch) + diff * sv
                full += beam + diff
    return got / full


def main() -> None:
    h0 = float(sys.argv[1]) if len(sys.argv) > 1 else 0.75
    mod_len = float(sys.argv[2]) if len(sys.argv) > 2 else 1.64
    print(f"lower edge {h0} m, module length up the slope {mod_len} m")
    for sname, season in SEASONS.items():
        for design in DESIGNS:
            print(f"  {sname:34s} {design:15s} L = {light_fraction(design, season, h0, mod_len):.3f}")


if __name__ == "__main__":
    main()
