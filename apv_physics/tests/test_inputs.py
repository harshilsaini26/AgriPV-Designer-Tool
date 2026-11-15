# tests/test_inputs.py
import numpy as np
import pytest
from helpers import weather

from apv_physics import BIFACIAL, MONOFACIAL, Kind, Layout, Losses, Module


def fixed(**kw):
    base = {
        "kind": Kind.FIXED,
        "module": BIFACIAL,
        "height_m": 3.0,
        "collector_width_m": 4.56,
        "tilt_deg": 20.0,
    }
    base.update(kw)
    return Layout(**base)


def test_presets():
    assert BIFACIAL == Module(0.225, 0.80, -0.0030)
    assert MONOFACIAL == Module(0.210, 0.0, -0.0035)


def test_kind_accepts_string():
    assert fixed(kind="fixed").kind is Kind.FIXED


@pytest.mark.parametrize(
    "field, value",
    [
        ("tilt_deg", 40.1),
        ("tilt_deg", -1.0),
        ("azimuth_deg", 89.0),
        ("azimuth_deg", 271.0),
        ("height_m", 0.4),
        ("height_m", 6.1),
        ("collector_width_m", 0.4),
        ("collector_width_m", 10.1),
    ],
)
def test_fixed_limits_name_the_field(field, value):
    with pytest.raises(ValueError, match=f"^{field}"):
        fixed(**{field: value})


def test_tracker_limits():
    Layout(Kind.TRACKER, BIFACIAL, height_m=2.5, collector_width_m=2.28, max_angle_deg=55.0)
    with pytest.raises(ValueError, match="^max_angle_deg"):
        Layout(Kind.TRACKER, BIFACIAL, height_m=2.5, collector_width_m=2.28, max_angle_deg=61.0)
    with pytest.raises(ValueError, match="^height_m"):  # lower edge within 0.3 m of the ground at full turn
        Layout(Kind.TRACKER, BIFACIAL, height_m=1.0, collector_width_m=2.28, max_angle_deg=55.0)


def test_tracker_ignores_fixed_only_fields():
    Layout(Kind.TRACKER, BIFACIAL, height_m=2.5, collector_width_m=2.28, tilt_deg=99.0)


def test_vertical_strip_limit():
    with pytest.raises(ValueError, match="^unfarmed_strip_m"):
        Layout(
            Kind.VERTICAL,
            BIFACIAL,
            height_m=0.8,
            collector_width_m=2.27,
            azimuth_deg=90.0,
            unfarmed_strip_m=3.5,
        )


@pytest.mark.parametrize("args", [(0.14, 0.8, -0.003), (0.22, 0.96, -0.003), (0.22, 0.8, -0.001)])
def test_module_limits(args):
    with pytest.raises(ValueError):
        Module(*args)


def test_center_height():
    assert fixed().center_height_m == pytest.approx(3.0 + 2.28 * np.sin(np.radians(20.0)))
    assert Layout(Kind.VERTICAL, BIFACIAL, 0.8, 2.27, azimuth_deg=90.0).center_height_m == pytest.approx(
        1.935
    )
    assert Layout(Kind.TRACKER, BIFACIAL, 2.5, 2.28).center_height_m == 2.5


def test_loss_factors():
    assert Losses().dc_factor == pytest.approx(0.93146328)
    assert Losses().ac_factor == pytest.approx(0.985)


def test_weather_arrays_are_readonly_float():
    w = weather()
    assert w.ghi.dtype == np.float64 and w.month.dtype == np.int8
    with pytest.raises(ValueError):
        w.ghi[0] = 1.0


@pytest.mark.parametrize(
    "kw",
    [
        {"ghi": np.array([1.0, 2.0])},
        {"month": np.array([0, 1, 2])},
        {"dni": np.array([1.0, np.nan, 2.0])},
        {"dhi": np.array([-1.0, 0.0, 0.0])},
    ],
)
def test_weather_validation(kw):
    with pytest.raises(ValueError):
        weather(**kw)


@pytest.mark.parametrize(
    "field, values",
    [
        ("dni_extra", [1360.0, 0.0, 1360.0]),
        ("zenith", [40.0, 95.0, 40.0]),
        ("zenith", [40.0, -1.0, 40.0]),
        ("azimuth", [180.0, -90.0, 180.0]),
        ("azimuth", [180.0, 400.0, 180.0]),
        ("wind_speed", [2.0, -10.0, 2.0]),
        ("temp_air", [25.0, 80.0, 25.0]),
        ("ghi", [500.0, 2500.0, 500.0]),
    ],
)
def test_weather_rejects_values_outside_physical_ranges(field, values):
    with pytest.raises(ValueError, match=f"^{field}"):
        weather(**{field: np.array(values)})


def test_default_direction_depends_on_the_structure():
    assert fixed().azimuth_deg == 180.0  # fixed rows face south
    assert Layout(Kind.VERTICAL, BIFACIAL, 0.8, 2.27).azimuth_deg == 90.0  # vertical rows face east and west
    assert Layout(Kind.VERTICAL, BIFACIAL, 0.8, 2.27, azimuth_deg=180.0).azimuth_deg == 180.0
