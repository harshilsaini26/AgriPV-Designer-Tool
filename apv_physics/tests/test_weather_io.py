import io
import json

import numpy as np
import pytest
from helpers import weather

from apv_physics.weather_io import load_meta, load_weather, save_weather


def test_round_trip_within_quantisation():
    w = weather(ghi=np.array([0.04, 512.34, 1099.96]), zenith=np.array([12.344, 45.0, 89.996]),
                azimuth=np.array([0.0, 181.237, 359.99]), temp_air=np.array([-12.34, 25.0, 47.96]))  # fmt: skip
    buf = io.BytesIO()
    save_weather(w, {"district": "Test", "attribution": "x"}, buf)
    buf.seek(0)
    r = load_weather(buf)
    np.testing.assert_allclose(r.ghi, w.ghi, atol=0.05)
    np.testing.assert_allclose(r.zenith, w.zenith, atol=0.005)
    np.testing.assert_allclose(r.azimuth, w.azimuth, atol=0.005)
    np.testing.assert_allclose(r.temp_air, w.temp_air, atol=0.05)
    assert (r.latitude, r.optimum_tilt_deg) == (26.0, 27.0)
    np.testing.assert_array_equal(r.month, w.month)


def test_meta_is_kept_and_extended():
    buf = io.BytesIO()
    save_weather(weather(), {"district": "Test"}, buf)
    buf.seek(0)
    meta = load_meta(buf)
    assert meta["district"] == "Test" and meta["pack_version"] == 1 and meta["elevation_m"] == 220.0


def test_load_from_path(tmp_path):
    p = tmp_path / "x.npz"
    save_weather(weather(), {}, p)
    assert load_weather(p).ghi.shape == (3,)


def test_unknown_version_rejected(tmp_path):
    p = tmp_path / "x.npz"
    save_weather(weather(), {}, p)
    d = dict(np.load(p))
    d["meta"] = np.array(json.dumps({**json.loads(str(d["meta"])), "pack_version": 2}))
    np.savez_compressed(p, **d)
    with pytest.raises(ValueError, match="unsupported weather pack version"):
        load_weather(p)
