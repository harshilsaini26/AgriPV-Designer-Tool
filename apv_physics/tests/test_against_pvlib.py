"""The engine against pvlib on the same weather and settings (design spec §7, V1)."""

from pathlib import Path

import numpy as np
import pytest
from apv_core.constants import GCR_GRID
from reference import pvlib_reference

from apv_physics import BIFACIAL, MONOFACIAL, Kind, Layout, Losses, load_weather, simulate

DATA = Path(__file__).parent / "data"
DISTRICTS = ["107_jodhpur", "555_ernakulam", "9_leh_ladakh"]
GCRS = [0.05, 0.25, 0.50]

LAYOUTS = {
    f"fixed-tilt{tilt:.0f}-az{az:.0f}-{name}": Layout(
        Kind.FIXED, module, 3.0, 4.56, tilt_deg=tilt, azimuth_deg=az
    )
    for tilt in (10.0, 25.0)
    for az in (180.0, 135.0)
    for name, module in (("mono", MONOFACIAL), ("bifacial", BIFACIAL))
}
LAYOUTS["tracker-45"] = Layout(Kind.TRACKER, BIFACIAL, 2.5, 2.28, max_angle_deg=45.0)
LAYOUTS["tracker-55"] = Layout(Kind.TRACKER, BIFACIAL, 2.5, 2.28, max_angle_deg=55.0)
LAYOUTS["vertical-ew"] = Layout(Kind.VERTICAL, BIFACIAL, 0.8, 2.27, azimuth_deg=90.0)


@pytest.fixture(scope="module", params=DISTRICTS)
def weather(request):
    return load_weather(DATA / f"{request.param}.npz")


@pytest.mark.parametrize("name", list(LAYOUTS))
def test_engine_matches_pvlib(weather, name):
    layout, losses = LAYOUTS[name], Losses()
    result = simulate(weather, layout, losses)
    for gcr in GCRS:
        i = GCR_GRID.index(gcr)
        ref_energy, ref_light = pvlib_reference(weather, layout, gcr, losses)
        energy, light = result.table.energy_kwh_per_kwp[i], result.table.light_fraction[i]
        where = f"{name} at GCR {gcr}"
        assert energy.sum() == pytest.approx(ref_energy.sum(), rel=0.01), f"annual energy, {where}"
        np.testing.assert_allclose(energy, ref_energy, rtol=0.02, err_msg=f"monthly energy, {where}")
        np.testing.assert_allclose(light, ref_light, atol=0.01, err_msg=f"ground light, {where}")
