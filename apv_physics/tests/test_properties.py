"""Properties that must hold for every valid layout (design spec §8), checked on the Ernakulam sample year."""

import math
from dataclasses import replace
from pathlib import Path

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from apv_physics import Kind, Layout, Module, load_weather, simulate

WEATHER = load_weather(Path(__file__).parent / "data" / "555_ernakulam.npz")
SETTINGS = settings(max_examples=25, deadline=None)


def floats(lo: float, hi: float):
    return st.floats(lo, hi, allow_nan=False, allow_infinity=False)


modules = st.builds(
    Module,
    efficiency=floats(0.15, 0.25),
    bifaciality=floats(0.0, 0.95),
    temp_coeff_per_c=floats(-0.005, -0.002),
)
fixed_layouts = st.builds(
    Layout,
    kind=st.just(Kind.FIXED),
    module=modules,
    height_m=floats(0.5, 6.0),
    collector_width_m=floats(0.5, 10.0),
    tilt_deg=floats(0.0, 40.0),
    azimuth_deg=floats(90.0, 270.0),
)


@st.composite
def tracker_layouts(draw):
    width = draw(floats(0.5, 10.0))
    max_angle = draw(floats(30.0, 60.0))
    lowest_axis = max(0.5, 0.3 + width / 2 * math.sin(math.radians(max_angle)) + 1e-6)
    return Layout(Kind.TRACKER, draw(modules), draw(floats(lowest_axis, 6.0)), width, max_angle_deg=max_angle)


@st.composite
def vertical_layouts(draw):
    width = draw(floats(0.5, 10.0))
    strip = draw(
        floats(0.0, min(3.0, 1.9 * width))
    )  # must leave farmed ground at GCR 0.50 (pitch = 2 x width)
    return Layout(
        Kind.VERTICAL,
        draw(modules),
        draw(floats(0.5, 6.0)),
        width,
        azimuth_deg=draw(floats(90.0, 270.0)),
        unfarmed_strip_m=strip,
    )


any_layout = st.one_of(fixed_layouts, tracker_layouts(), vertical_layouts())


@SETTINGS
@given(any_layout)
def test_light_on_the_whole_ground_never_rises_with_gcr(layout):
    # A law only when all the ground counts. With an unfarmed strip under vertical rows the farmed band can
    # gain light between two densities, because row shadows land on the unfarmed strip: up to 0.24 in one
    # month when the band is under about 0.5 m wide, none for the preset layout (see test_simulate).
    if layout.kind is Kind.VERTICAL:
        layout = replace(layout, unfarmed_strip_m=0.0)
    light = simulate(WEATHER, layout).table.light_fraction
    assert (np.diff(light, axis=0) <= 1e-9).all()


@SETTINGS
@given(fixed_layouts, floats(0.5, 6.0), floats(0.5, 10.0))
def test_mean_light_ignores_height_and_width(layout, height, width):
    other = Layout(Kind.FIXED, layout.module, height, width, layout.tilt_deg, layout.azimuth_deg)
    a = simulate(WEATHER, layout).table.light_fraction
    b = simulate(WEATHER, other).table.light_fraction
    np.testing.assert_allclose(a, b, atol=0.005)


@SETTINGS
@given(any_layout)
def test_darkest_tenth_not_above_mean(layout):
    r = simulate(WEATHER, layout)
    assert (r.light_darkest_tenth <= r.table.light_fraction + 1e-9).all()


@SETTINGS
@given(fixed_layouts)
def test_fixed_energy_never_rises_with_gcr(layout):
    annual = simulate(WEATHER, layout).table.energy_kwh_per_kwp.sum(axis=1)
    assert (np.diff(annual[1:]) <= 1e-6).all()


@SETTINGS
@given(any_layout)
def test_outputs_finite_and_in_range(layout):
    r = simulate(WEATHER, layout)
    energy, light = r.table.energy_kwh_per_kwp, r.table.light_fraction
    assert np.isfinite(energy).all() and (energy >= 0).all()
    assert ((light >= 0) & (light <= 1)).all()
    assert ((r.light_darkest_tenth >= 0) & (r.light_darkest_tenth <= 1)).all()
    assert (r.clear_gap_m[1:] >= 0).all()
