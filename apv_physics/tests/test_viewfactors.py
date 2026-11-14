import numpy as np
import pytest
from pvlib.bifacial import utils as pv

from apv_physics import viewfactors as vf

TILTS = [0.0, 10.0, 25.0, 55.0, 90.0, 125.0, 170.0]
GCRS = [0.05, 0.25, 0.5]


@pytest.mark.parametrize("gcr", GCRS)
def test_row_view_factors_match_pvlib(gcr):
    t = np.array(TILTS)
    np.testing.assert_allclose(vf.vf_row_sky_2d_integ(t, gcr), pv.vf_row_sky_2d_integ(t, gcr), rtol=1e-9)
    np.testing.assert_allclose(
        vf.vf_row_ground_2d_integ(t, gcr), pv.vf_row_ground_2d_integ(t, gcr), rtol=1e-9
    )


@pytest.mark.parametrize("gcr", GCRS)
@pytest.mark.parametrize("height", [0.75, 3.0, 6.0])
def test_ground_sky_view_matches_pvlib(gcr, height):
    pitch = 4.56 / gcr
    rot = np.array([-55.0, -20.0, 0.0, 20.0, 55.0, 90.0])
    x = np.linspace(0.005, 0.995, 100)
    np.testing.assert_allclose(vf.vf_ground_sky_2d(rot, gcr, x, pitch, height),
                               pv.vf_ground_sky_2d(rot, gcr, x, pitch, height), rtol=1e-9)  # fmt: skip
    np.testing.assert_allclose(vf.vf_ground_sky_2d_integ(rot, gcr, height, pitch),
                               pv.vf_ground_sky_2d_integ(rot, gcr, height, pitch), rtol=1e-9)  # fmt: skip


def test_unshaded_ground_fraction_matches_pvlib():
    rot = np.array([20.0, 20.0, -40.0, 0.0])
    phi = np.array([-60.0, 30.0, 10.0, 0.0])
    np.testing.assert_allclose(
        vf.unshaded_ground_fraction(rot, phi, 0.4), pv._unshaded_ground_fraction(rot, phi, 0.4)
    )


def test_projection_tangent():
    assert vf.solar_projection_tangent(45.0, 180.0, 180.0) == pytest.approx(1.0)
    assert vf.solar_projection_tangent(45.0, 90.0, 180.0) == pytest.approx(0.0, abs=1e-12)


def test_known_values():
    # the whole sky is visible from flat panels; none of it from the underside
    assert vf.vf_row_sky_2d_integ(0.0, 0.4) == pytest.approx(1.0)
    assert vf.vf_row_sky_2d_integ(180.0, 0.4) == pytest.approx(0.0, abs=1e-12)
