import numpy as np
import pandas as pd

from pipeline.weather.build_packs import make_weather


def frame():
    # one June day at Jodhpur, hourly UTC stamps; irradiance filled from a simple clear-sky shape
    t = pd.date_range("2019-06-21 00:00", periods=24, freq="h", tz="UTC")
    ghi = np.clip(1000 * np.sin(np.pi * (np.arange(24) - 0.5) / 13.5), 0, None)
    ghi[14:] = 0.0
    return pd.DataFrame({"time_utc": t.strftime("%Y%m%d:%H%M"), "ghi": ghi, "dni": ghi * 0.8, "dhi": ghi * 0.3,
                         "temp_air": 35.0, "wind_speed": 2.0})  # fmt: skip


def test_keeps_daylight_rows_only():
    w = make_weather(frame(), 26.35, 73.10, 222.0, 27.0)
    assert len(w.ghi) == int((frame()["ghi"] > 0).sum())
    assert (w.ghi > 0).all() and set(w.month.tolist()) == {6}


def test_sun_position_is_plausible():
    w = make_weather(frame(), 26.35, 73.10, 222.0, 27.0)
    i = int(np.argmin(w.zenith))
    assert w.zenith[i] < 6.0  # near-overhead at the June solstice, close to the tropic
    assert 1300 < w.dni_extra[0] < 1340  # Earth is far from the sun in June
    assert w.optimum_tilt_deg == 27.0 and w.elevation_m == 222.0
