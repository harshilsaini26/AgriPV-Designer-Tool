import time

import numpy as np
import pytest
from apv_core.physics import kwp_per_acre
from helpers import weather

from apv_physics import (
    BIFACIAL,
    MONOFACIAL,
    Kind,
    Layout,
    load_weather,
    reference_energy_kwh_per_acre,
    simulate,
)

DATA = __import__("pathlib").Path(__file__).parent / "data"
JODHPUR = load_weather(DATA / "107_jodhpur.npz")
FIXED = Layout(Kind.FIXED, BIFACIAL, height_m=3.0, collector_width_m=4.56, tilt_deg=20.0)
TRACKER = Layout(Kind.TRACKER, BIFACIAL, height_m=2.5, collector_width_m=2.28)
VERTICAL = Layout(Kind.VERTICAL, BIFACIAL, height_m=0.8, collector_width_m=2.27, azimuth_deg=90.0)


@pytest.mark.parametrize("layout", [FIXED, TRACKER, VERTICAL])
def test_shapes_and_open_field_row(layout):
    r = simulate(JODHPUR, layout)
    assert r.table.energy_kwh_per_kwp.shape == (11, 12) and r.light_darkest_tenth.shape == (11, 12)
    assert (r.table.energy_kwh_per_kwp[0] == 0).all() and (r.table.light_fraction[0] == 1).all()
    assert (r.light_darkest_tenth[0] == 1).all() and np.isinf(r.clear_gap_m[0])
    assert np.isfinite(r.table.energy_kwh_per_kwp).all()


def test_jodhpur_fixed_is_plausible():
    r = simulate(JODHPUR, Layout(Kind.FIXED, MONOFACIAL, 3.0, 4.56, tilt_deg=25.0))
    annual = r.table.energy_kwh_per_kwp.sum(axis=1)
    assert 1600 < annual[1] < 1950  # Global Solar Atlas gives 1,752 at the optimum tilt
    light = r.table.light_fraction.mean(axis=1)
    assert 0.65 < light[5] < 0.80 and 0.45 < light[9] < 0.60  # GCR 0.25 and 0.45


def test_tracker_beats_fixed_and_vertical_trails():
    e = {k: simulate(JODHPUR, l).table.energy_kwh_per_kwp[5].sum() for k, l in
         {"fixed": FIXED, "tracker": TRACKER, "vertical": VERTICAL}.items()}  # fmt: skip
    assert e["tracker"] > e["fixed"] > e["vertical"]


def test_clear_gap():
    r = simulate(JODHPUR, FIXED)
    assert r.clear_gap_m[5] == pytest.approx(4.56 / 0.25 - 4.56 * np.cos(np.radians(20.0)))
    assert simulate(JODHPUR, TRACKER).clear_gap_m[10] == pytest.approx(2.28 / 0.5 - 2.28)


def test_reference_plant():
    ref = reference_energy_kwh_per_acre(JODHPUR, BIFACIAL)
    assert simulate(JODHPUR, FIXED).table.ref_energy_kwh_per_acre == pytest.approx(ref)
    assert 1500 * kwp_per_acre(0.45, 0.225) < ref < 2100 * kwp_per_acre(0.45, 0.225)


def test_missing_month_is_safe():
    r = simulate(weather(n=6, month=np.array([1, 1, 1, 7, 7, 7])), FIXED)
    assert (r.table.energy_kwh_per_kwp[:, 3] == 0).all() and (r.table.light_fraction[:, 3] == 1).all()


@pytest.mark.parametrize("layout", [
    Layout(Kind.FIXED, BIFACIAL, 6.0, 0.5, tilt_deg=20.0),
    Layout(Kind.FIXED, BIFACIAL, 0.5, 10.0, tilt_deg=20.0),
    Layout(Kind.FIXED, MONOFACIAL, 2.0, 4.56, tilt_deg=0.0),
    Layout(Kind.FIXED, BIFACIAL, 3.0, 4.56, tilt_deg=40.0, azimuth_deg=90.0),
    Layout(Kind.TRACKER, BIFACIAL, 6.0, 0.5, max_angle_deg=60.0),
])  # fmt: skip
def test_limit_corners(layout):
    simulate(JODHPUR, layout)  # warm-up
    t = time.perf_counter()
    r = simulate(JODHPUR, layout)
    assert time.perf_counter() - t < 2.0
    assert np.isfinite(r.table.energy_kwh_per_kwp).all()
    assert ((r.table.light_fraction >= 0) & (r.table.light_fraction <= 1)).all()


@pytest.mark.parametrize("layout", [FIXED, TRACKER, VERTICAL])
def test_speed(layout):
    simulate(JODHPUR, layout)  # warm-up
    t = time.perf_counter()
    simulate(JODHPUR, layout)
    assert time.perf_counter() - t < 2.0


def test_no_heavy_imports():
    import subprocess
    import sys

    code = "import sys, apv_physics; print(any(m in sys.modules for m in ('pandas', 'scipy', 'pvlib')))"
    assert (
        subprocess.run(
            [sys.executable, "-c", code], check=True, capture_output=True, text=True
        ).stdout.strip()
        == "False"
    )
