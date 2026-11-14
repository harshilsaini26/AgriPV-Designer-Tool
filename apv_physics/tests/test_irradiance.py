import numpy as np
import pvlib
import pytest
from pvlib.bifacial import infinite_sheds

from apv_physics import load_weather
from apv_physics.irradiance import effective_irradiance, iam_beam, iam_diffuse, panel_irradiance

DATA = __import__("pathlib").Path(__file__).parent / "data"
KEYS = {"front_direct": "poa_front_direct", "front_sky": "poa_front_sky_diffuse",
        "front_ground": "poa_front_ground_diffuse", "back_direct": "poa_back_direct",
        "back_sky": "poa_back_sky_diffuse", "back_ground": "poa_back_ground_diffuse"}  # fmt: skip


def test_iam_beam_values():
    np.testing.assert_allclose(iam_beam(np.array([0.0, 30.0, 60.0, 80.0, 90.0])),
                               [1.0, 0.997466, 0.957912, 0.663481, 0.0], atol=1e-6)  # fmt: skip


def test_iam_diffuse_values():
    sky, ground = iam_diffuse(np.array([20.0, 90.0, 160.0]))
    np.testing.assert_allclose(sky, [0.953406, 0.951460, 0.673630], atol=1e-6)
    np.testing.assert_allclose(ground, [0.673630, 0.951460, 0.953406], atol=1e-6)


def test_single_hour_reference():
    p = panel_irradiance(20.0, 180.0, np.array([40.0]), np.array([150.0]), 0.4, 3.0, 11.4, np.array([700.0]),
                         np.array([150.0]), np.array([720.0]), np.array([1360.0]), 0.2)  # fmt: skip
    expected = {"front_direct": 749.7316, "front_sky": 67.1522, "front_ground": 1.6045, "back_direct": 0.0,
                "back_sky": 1.5298, "back_ground": 71.026}  # fmt: skip
    for k, v in expected.items():
        assert p[k][0] == pytest.approx(v, abs=1e-3), k


@pytest.mark.parametrize("tilt, az, gcr", [(10.0, 180.0, 0.05), (25.0, 135.0, 0.5), (90.0, 90.0, 0.25)])
def test_fixed_matches_pvlib_on_a_real_year(tilt, az, gcr):
    w = load_weather(DATA / "555_ernakulam.npz")
    pitch = 4.56 / gcr
    ours = panel_irradiance(
        tilt, az, w.zenith, w.azimuth, gcr, 3.0, pitch, w.ghi, w.dhi, w.dni, w.dni_extra, 0.2
    )
    ref = infinite_sheds.get_irradiance(tilt, az, w.zenith, w.azimuth, gcr, 3.0, pitch, w.ghi, w.dhi, w.dni,
                                        albedo=0.2, model="haydavies", dni_extra=w.dni_extra)  # fmt: skip
    for k, pk in KEYS.items():
        np.testing.assert_allclose(ours[k], np.nan_to_num(ref[pk]), rtol=1e-6, atol=1e-6, err_msg=k)


def test_tracker_interpolation_is_close_to_pvlib():
    w = load_weather(DATA / "107_jodhpur.npz")
    tr = pvlib.tracking.singleaxis(
        w.zenith, w.azimuth, axis_tilt=0, axis_azimuth=180, max_angle=55, backtrack=True, gcr=0.3
    )
    tilt, az = np.nan_to_num(tr["surface_tilt"]), np.nan_to_num(tr["surface_azimuth"], nan=90.0)
    ours = panel_irradiance(
        tilt, az, w.zenith, w.azimuth, 0.3, 2.5, 7.6, w.ghi, w.dhi, w.dni, w.dni_extra, 0.2
    )
    ref = infinite_sheds.get_irradiance(tilt, az, w.zenith, w.azimuth, 0.3, 2.5, 7.6, w.ghi, w.dhi, w.dni,
                                        albedo=0.2, model="haydavies", dni_extra=w.dni_extra)  # fmt: skip
    for k, pk in KEYS.items():
        assert ours[k].sum() == pytest.approx(np.nansum(ref[pk]), rel=2e-3, abs=1.0), k


def test_no_nan_at_grazing_sun():
    z, a = (
        np.array([89.99, 89.99, 60.0]),
        np.array([180.0, 90.0, 0.0]),
    )  # horizon ahead; in a vertical panel's plane
    one = np.ones(3)
    for tilt, az in ((20.0, 180.0), (90.0, 90.0)):
        p = panel_irradiance(tilt, az, z, a, 0.5, 2.0, 4.0, 50 * one, 40 * one, 300 * one, 1360 * one, 0.2)
        assert all(np.isfinite(v).all() and (v >= 0).all() for k, v in p.items())


def test_effective_irradiance_adds_rear_gain():
    p = panel_irradiance(20.0, 180.0, np.array([40.0]), np.array([150.0]), 0.4, 3.0, 11.4, np.array([700.0]),
                         np.array([150.0]), np.array([720.0]), np.array([1360.0]), 0.2)  # fmt: skip
    mono = effective_irradiance(p, 20.0, 0.0, 0.05)
    bif = effective_irradiance(p, 20.0, 0.8, 0.05)
    assert mono[0] < p["front_direct"][0] + p["front_sky"][0] + p["front_ground"][0]  # reflection loss
    assert bif[0] > mono[0]
