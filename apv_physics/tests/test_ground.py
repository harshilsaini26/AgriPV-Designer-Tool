import numpy as np
import pytest
from helpers import weather
from pvlib.bifacial import utils as pv

from apv_physics import load_weather
from apv_physics.ground import N_STRIPS, farmed_mask, ground_light, strip_sky_view, strip_unshaded

DATA = __import__("pathlib").Path(__file__).parent / "data"
ALL = np.ones(N_STRIPS, dtype=bool)


def test_overhead_sun_flat_panels_shade_equals_density():
    u = strip_unshaded(np.array([0.0]), np.array([0.0]), 0.30, 3.0, 10.0)
    assert u.shape == (1, 100)
    assert (u[0] < 1e-9).sum() == 30 and (u[0] > 1 - 1e-9).sum() == 70
    np.testing.assert_allclose(u[0, :15], 0.0, atol=1e-9)  # the shadow is centred under the row
    np.testing.assert_allclose(u[0, -15:], 0.0, atol=1e-9)


def test_partly_shaded_strip_is_fractional():
    u = strip_unshaded(np.array([0.0]), np.array([0.0]), 0.25, 3.0, 10.0)  # shadow edge at 1.25 m, mid-strip
    assert u[0, 12] == pytest.approx(0.5) and u[0].mean() == pytest.approx(0.75)


def test_shadow_moves_with_the_sun():
    # flat row at 3 m, tan(phi) = 1: the shadow shifts 3 m along +x
    u = strip_unshaded(np.array([0.0]), np.array([1.0]), 0.20, 3.0, 10.0)
    np.testing.assert_allclose(u[0, 20:40], 0.0, atol=1e-9)
    assert u[0].mean() == pytest.approx(0.8)


def test_tilted_row_shadow_length():
    # width 4, tilt 30 deg, tan(phi) = 1: edges at x = +-1.732, z = 3 +- 1 -> shadows at 5.732 and 0.268
    u = strip_unshaded(np.array([30.0]), np.array([1.0]), 0.4, 3.0, 10.0)
    assert u[0].mean() == pytest.approx(1 - 5.4641 / 10.0, abs=1e-4)


@pytest.mark.parametrize("height", [0.75, 2.5, 6.0])
def test_mean_matches_energy_balance_for_any_height(height):
    rot, tan_phi = np.array([20.0, 20.0, -35.0]), np.array([-2.5, 0.7, 8.0])
    u = strip_unshaded(rot, tan_phi, 0.4, height, 11.4)
    w = 0.4 * 11.4
    length = np.minimum(np.abs(w * np.cos(np.radians(rot)) + w * np.sin(np.radians(rot)) * tan_phi), 11.4)
    np.testing.assert_allclose(u.mean(axis=1), 1 - length / 11.4, atol=1e-9)


def test_grazing_sun_is_finite():
    u = strip_unshaded(np.array([20.0, 90.0]), np.array([5e3, -5e3]), 0.5, 2.0, 4.0)
    assert np.isfinite(u).all() and (u >= 0).all() and (u <= 1).all()


def test_sky_view_matches_pvlib_and_shapes():
    v = strip_sky_view(20.0, 0.4, 3.0, 11.4)
    x = (np.arange(100) + 0.5) / 100
    ref = pv.vf_ground_sky_2d(20.0, 0.4, x, 11.4, 3.0, max_rows=np.ceil(3.0 / (11.4 * np.tan(np.radians(5)))))
    np.testing.assert_allclose(v, np.ravel(ref), rtol=1e-9)
    rot = np.array([-50.0, 0.3, 12.2, 55.0])
    assert strip_sky_view(rot, 0.4, 2.5, 5.7).shape == (4, 100)


def test_farmed_mask():
    assert farmed_mask(10.0, 0.0).all()
    m = farmed_mask(10.0, 1.0)  # 0.5 m either side of the row centre
    assert (~m).sum() == 10 and not m[:5].any() and not m[-5:].any() and m[5:95].all()


def test_no_farmed_ground_raises():
    with pytest.raises(ValueError, match="^unfarmed_strip_m"):
        farmed_mask(1.0, 3.0)


def test_open_sky_gives_one():
    w = weather(n=4, month=np.array([1, 1, 7, 7]))
    mean, dark = ground_light(w, 0.0, 180.0, 1e-6, 3.0, 1e-5, ALL)
    # not exactly 1: the ported sky view leaves out the sky within about 5 degrees of the horizon
    assert mean[0] == pytest.approx(1.0, abs=2e-3) and mean[6] == pytest.approx(1.0, abs=2e-3)
    assert mean[3] == 1.0 and dark[3] == 1.0  # a month with no hours


def test_real_year_ranges_and_evenness():
    w = load_weather(DATA / "107_jodhpur.npz")
    low_mean, low_dark = ground_light(w, 20.0, 180.0, 0.4, 2.5 + 0.78, 4.56, ALL)
    high_mean, high_dark = ground_light(w, 20.0, 180.0, 0.4, 6.0 + 0.78, 4.56, ALL)
    assert ((0 < low_mean) & (low_mean < 1)).all() and (low_dark <= low_mean + 1e-12).all()
    np.testing.assert_allclose(low_mean, high_mean, atol=0.005)  # height does not change the mean
    assert high_dark.mean() > low_dark.mean()  # taller rows give more even light


def test_mean_close_to_pvlib_reference():
    w = load_weather(DATA / "555_ernakulam.npz")
    gcr, tilt, pitch, h = 0.25, 15.0, 4.56 / 0.25, 3.0
    mean, _ = ground_light(w, tilt, 180.0, gcr, h, 4.56, ALL)
    ai = np.clip(w.dni / w.dni_extra, 0, 1)
    beam, iso = w.dni * np.clip(np.cos(np.radians(w.zenith)), 0, None) + w.dhi * ai, w.dhi * (1 - ai)
    phi = np.degrees(np.arctan(pv._solar_projection_tangent(w.zenith, w.azimuth, 180.0)))
    f = pv._unshaded_ground_fraction(tilt, phi, gcr, max_zenith=90)
    v = pv.vf_ground_sky_2d_integ(tilt, gcr, h, pitch)
    assert mean.mean() == pytest.approx(((beam * f).sum() + iso.sum() * v) / (beam + iso).sum(), abs=0.01)
