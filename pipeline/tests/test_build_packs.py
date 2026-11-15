import numpy as np
import pandas as pd
import pvlib
import pytest

from pipeline.weather.build_packs import check_weather, derive_hourly, make_weather

LAT, LON, ELEV = 26.35, 73.10, 222.0  # Jodhpur
DAY = pd.Timestamp("2019-06-21 00:00", tz="UTC")  # sunrise about 00:15 UTC, sunset about 13:55 UTC


def sun(times):
    return pvlib.solarposition.get_solarposition(pd.DatetimeIndex(times), LAT, LON, altitude=ELEV)


def frame():
    """One June day, hourly UTC stamps. Each value is the hour's mean, so it belongs to the stamp + 30 min."""
    t = pd.date_range(DAY, periods=24, freq="h")
    cos_mid = np.clip(
        np.cos(np.radians(sun(t + pd.Timedelta(minutes=30))["apparent_zenith"].to_numpy())), 0, None
    )
    ghi = 800.0 * cos_mid
    return pd.DataFrame(
        {
            "time_utc": t.strftime("%Y%m%d:%H%M"),
            "ghi": ghi,
            "dni": ghi * 0.9,  # as published: not trusted, the builder derives its own
            "dhi": ghi * 0.25,
            "temp_air": 35.0,
            "wind_speed": 2.0,
        }
    )


def test_keeps_daylight_rows_only():
    w = make_weather(frame(), LAT, LON, ELEV, 27.0)
    assert len(w.ghi) == int((frame()["ghi"] > 0).sum())
    assert (w.ghi > 0).all() and set(w.month.tolist()) == {6}


def test_metadata_and_extraterrestrial_light():
    w = make_weather(frame(), LAT, LON, ELEV, 27.0)
    assert 1300 < w.dni_extra[0] < 1340  # Earth is far from the sun in June
    assert w.optimum_tilt_deg == 27.0 and w.elevation_m == 222.0


def test_sun_is_taken_half_an_hour_after_the_stamp():
    hourly = derive_hourly(frame(), LAT, LON, ELEV)
    ref = sun([DAY + pd.Timedelta(hours=7, minutes=30)])
    assert hourly["zenith"].iloc[7] == pytest.approx(ref["apparent_zenith"].iloc[0], abs=1e-6)
    assert hourly["azimuth"].iloc[7] == pytest.approx(ref["azimuth"].iloc[0], abs=1e-6)
    assert len(hourly) == 24  # every hour is kept here; make_weather drops the dark ones


def test_sunrise_hour_uses_the_centre_of_its_sunlit_part():
    f = frame()
    f.loc[0, ["ghi", "dni", "dhi"]] = [20.0, 0.0, 15.0]  # the hour in which the sun rises
    hourly = derive_hourly(f, LAT, LON, ELEV)
    minutes = np.array([5, 15, 25, 35, 45, 55])
    up = sun(DAY + pd.to_timedelta(minutes, "min"))["apparent_zenith"].to_numpy() < 90
    centre = minutes[up].mean()
    assert 30 < centre < 60  # later than mid-hour, because the first minutes are dark
    ref = sun([DAY + pd.Timedelta(minutes=centre)])
    assert hourly["zenith"].iloc[0] == pytest.approx(ref["apparent_zenith"].iloc[0], abs=1e-6)
    assert hourly["zenith"].iloc[0] < 90


def test_direct_light_is_rederived_from_the_stored_sun():
    w = make_weather(frame(), LAT, LON, ELEV, 27.0)
    np.testing.assert_allclose(w.dni * np.cos(np.radians(w.zenith)) + w.dhi, w.ghi, atol=1e-6)
    assert (w.dni <= w.dni_extra + 1e-9).all() and (w.dhi <= w.ghi + 1e-9).all()
    assert (w.zenith < 90).all() and (w.dni >= 0).all()
    midday = int(np.argmin(w.zenith))
    assert w.dni[midday] == pytest.approx(800.0 * 0.75, rel=1e-6)  # (ghi - dhi) / cos z = 0.75 x 800


def test_direct_light_is_capped_and_the_rest_becomes_sky_light():
    f = frame()
    f.loc[1, ["ghi", "dhi"]] = [400.0, 10.0]  # far more direct light than the low sun can deliver
    w = make_weather(f, LAT, LON, ELEV, 27.0)
    assert w.dni[1] == pytest.approx(w.dni_extra[1])
    assert w.dhi[1] > 10.0
    assert w.dni[1] * np.cos(np.radians(w.zenith[1])) + w.dhi[1] == pytest.approx(400.0)


def test_negative_wind_is_clipped():
    f = frame()
    f["wind_speed"] = -1.5
    assert (make_weather(f, LAT, LON, ELEV, 27.0).wind_speed == 0.0).all()


def test_check_passes_aligned_weather():
    assert check_weather(make_weather(frame(), LAT, LON, ELEV, 27.0)) == []


def test_check_flags_sunlight_out_of_step_with_the_sun():
    f = frame()
    for col in ("ghi", "dni", "dhi"):
        f[col] = np.roll(f[col].to_numpy(), -1)  # every value stamped one hour too early
    problems = check_weather(make_weather(f, LAT, LON, ELEV, 27.0))
    assert any("morning" in p for p in problems)
