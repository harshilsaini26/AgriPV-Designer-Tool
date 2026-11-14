import numpy as np
import pvlib
import pytest

from apv_physics import Losses
from apv_physics.power import ac_power_per_kwp, cell_temperature, dc_power_per_kwp

NO_LOSS = Losses(soiling=0.0, mismatch=0.0, dc_wiring=0.0, connections=0.0, ac_wiring=0.0)


def test_cell_temperature():
    assert cell_temperature(np.array([800.0]), np.array([20.0]), np.array([1.0]))[0] == pytest.approx(
        45.125628
    )


def test_dc_power():
    assert dc_power_per_kwp(np.array([1000.0]), np.array([25.0]), -0.003)[0] == pytest.approx(1000.0)
    assert dc_power_per_kwp(np.array([800.0]), np.array([45.0]), -0.003)[0] == pytest.approx(752.0)
    assert dc_power_per_kwp(np.array([100.0]), np.array([400.0]), -0.005)[0] == 0.0


def test_inverter_without_other_losses():
    out = ac_power_per_kwp(np.array([500.0, 100.0, 1000.0, 0.0]), NO_LOSS)
    np.testing.assert_allclose(out, [491.293945, 95.147784, 800.0, 0.0], atol=1e-5)


def test_default_losses_match_pvlib():
    p = np.linspace(0.0, 1100.0, 56)
    L = Losses()
    ref = pvlib.inverter.pvwatts(p * L.dc_factor, 800.0 / 0.98, eta_inv_nom=0.98) * L.ac_factor
    np.testing.assert_allclose(ac_power_per_kwp(p, L), ref, atol=1e-9)
    assert ac_power_per_kwp(p, L).max() == pytest.approx(800.0 * 0.985)
