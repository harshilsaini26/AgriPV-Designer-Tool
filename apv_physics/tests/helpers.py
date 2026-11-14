# tests/helpers.py
import numpy as np

from apv_physics import Weather


def weather(n=3, **kw):
    base = {
        "month": np.ones(n),
        "ghi": np.full(n, 500.0),
        "dni": np.full(n, 600.0),
        "dhi": np.full(n, 100.0),
        "temp_air": np.full(n, 25.0),
        "wind_speed": np.full(n, 2.0),
        "zenith": np.full(n, 40.0),
        "azimuth": np.full(n, 180.0),
        "dni_extra": np.full(n, 1360.0),
        "latitude": 26.0,
        "longitude": 73.0,
        "elevation_m": 220.0,
        "optimum_tilt_deg": 27.0,
    }
    base.update(kw)
    return Weather(**base)
