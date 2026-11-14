import numpy as np
import pvlib
import pytest

from apv_physics import load_weather
from apv_physics.tracking import tracker_rotation

DATA = __import__("pathlib").Path(__file__).parent / "data"


@pytest.mark.parametrize(
    "zen, az, expected",
    [(30.0, 180.0, 0.0), (80.0, 90.0, -15.7293), (60.0, 110.0, -55.0), (70.0, 260.0, 39.79)],
)
def test_hand_values(zen, az, expected):
    assert tracker_rotation(np.array([zen]), np.array([az]), 0.4, 55.0)[0] == pytest.approx(
        expected, abs=1e-3
    )


def test_sun_on_axis_gives_flat():
    out = tracker_rotation(np.array([0.0, 45.0, 45.0]), np.array([123.0, 180.0, 0.0]), 0.3, 55.0)
    np.testing.assert_allclose(out, 0.0, atol=1e-9)


def test_below_horizon_is_zero():
    assert tracker_rotation(np.array([95.0]), np.array([80.0]), 0.3, 55.0)[0] == 0.0


def test_backtracking_keeps_rows_out_of_each_others_shade():
    # with no turning limit, the row shadow never reaches past the next row:
    # gcr * cos(theta - theta_true) <= |cos(theta_true)|
    w = load_weather(DATA / "107_jodhpur.npz")
    true = np.degrees(np.arctan2(np.sin(np.radians(w.zenith)) * np.sin(np.radians(w.azimuth - 180.0)),
                                 np.cos(np.radians(w.zenith))))  # fmt: skip
    theta = tracker_rotation(w.zenith, w.azimuth, 0.4, 90.0)
    assert (0.4 * np.cos(np.radians(theta - true)) <= np.abs(np.cos(np.radians(true))) + 1e-9).all()


@pytest.mark.parametrize("gcr", [0.05, 0.25, 0.5])
def test_matches_pvlib_on_a_real_year(gcr):
    w = load_weather(DATA / "107_jodhpur.npz")
    ref = pvlib.tracking.singleaxis(w.zenith, w.azimuth, axis_tilt=0, axis_azimuth=180, max_angle=55,
                                    backtrack=True, gcr=gcr)["tracker_theta"]  # fmt: skip
    np.testing.assert_allclose(
        tracker_rotation(w.zenith, w.azimuth, gcr, 55.0), np.nan_to_num(ref), atol=1e-6
    )
