"""Build one weather pack per district from the calibrated hourly typical-year files (design spec §6).

Usage: python -m pipeline.weather.build_packs <research_dir> <out_dir>

Inputs, all under <research_dir>/08_solar_weather/tmy/:
- tmy_index.csv              district codes, point, elevation and file names
- tmy_opt_tilt.csv           Global Solar Atlas optimum tilt at each point (research/_scripts/gsa_opt_tilt_districts.py)
- tmy_calibration.csv        annual GHI and DHI after calibration, used to check each pack
- raw/pvgis_tmy_calibrated/  one hourly file per district (local, git-ignored)

Each pack holds the daylight hours only, with the sun's position for every hour computed here with pvlib, so
the live engine (apv_physics) needs no solar-position code.

Timing. PVGIS stamps each hour on the hour, but its ERA5 irradiance is the mean over the hour that follows
(`irradiance_time_offset` = 0.5 h in every PVGIS response). The sun is therefore taken half an hour after the
stamp, or at the centre of the sunlit part of the hour when the sun rises or sets in it. The direct normal
irradiance that PVGIS publishes is normalised with the sun at the stamp, which inflates it in the morning and
deflates it in the evening, so it is not used: direct light is re-derived from the horizontal values and the
stored sun.
"""

import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pvlib
from apv_physics import Weather, load_weather
from apv_physics.weather_io import PACK_VERSION, save_weather

DATA_VERSION = "2026-11-15"
ATTRIBUTION = (
    "Typical-year weather: PVGIS © European Union (JRC), PVGIS-ERA5 2005–2023; contains modified Copernicus "
    "Climate Change Service information (ERA5); calibrated to Global Solar Atlas 2.0 (Solargis / World Bank "
    "Group, CC BY 4.0)"
)
IRRADIANCE_TIME_OFFSET = pd.Timedelta(
    minutes=30
)  # PVGIS-ERA5: each value is the mean of the hour after the stamp
# annual totals against the calibration table (tmy_calibration.csv), as a share, with a floor of 1 kWh/m2
GHI_TOLERANCE = 0.001
DHI_TOLERANCE = 0.001

_SUB_HOUR_MINUTES = (5, 15, 25, 35, 45, 55)  # where the sun is sampled in an hour in which it rises or sets
_MAX_DAYLIGHT_ZENITH = 89.99  # degrees
_MIN_COS_ZENITH = 0.0349  # cos 88 deg: below a 2 degree sun, direct light is not scaled up any further
_LOW_SUN_COS = (0.05, 0.35)  # the band of sun heights used to compare morning with afternoon
_AM_PM_CLEARNESS_RATIO = (0.4, 2.5)
_WEATHER_ARRAYS = ("month", "ghi", "dni", "dhi", "temp_air", "wind_speed", "zenith", "azimuth", "dni_extra")


def _sun(
    times: pd.DatetimeIndex, lat: float, lon: float, elevation_m: float
) -> tuple[np.ndarray, np.ndarray]:
    """Apparent zenith and azimuth of the sun at each time, in degrees."""
    sun = pvlib.solarposition.get_solarposition(times, lat, lon, altitude=elevation_m)
    return sun["apparent_zenith"].to_numpy().copy(), sun["azimuth"].to_numpy().copy()


def derive_hourly(df: pd.DataFrame, lat: float, lon: float, elevation_m: float) -> pd.DataFrame:
    """Every hour of one district's table with the sun's position and consistent direct and sky light.

    Columns: time_utc, month, ghi, dni, dhi, temp_air, wind_speed, zenith, azimuth, dni_extra. For each hour,
    `dni * cos(zenith) + dhi = ghi` holds exactly: direct normal light is the horizontal direct light divided
    by the cosine of the stored zenith, limited to the extraterrestrial value and to a sun at least 2 degrees
    up; whatever that limit removes is counted as sky light. Negative wind speeds are set to zero.
    """
    times = pd.DatetimeIndex(pd.to_datetime(df["time_utc"], format="%Y%m%d:%H%M", utc=True))
    ghi = np.clip(df["ghi"].to_numpy(dtype=float), 0.0, None)
    dhi = np.clip(df["dhi"].to_numpy(dtype=float), 0.0, ghi)
    dni_extra = np.asarray(pvlib.irradiance.get_extra_radiation(times), dtype=float)

    zenith, azimuth = _sun(times + IRRADIANCE_TIME_OFFSET, lat, lon, elevation_m)
    # hours in which the sun rises or sets: use the centre of the sunlit part, not mid-hour
    zenith_start, _ = _sun(times, lat, lon, elevation_m)
    zenith_end, _ = _sun(times + pd.Timedelta(hours=1), lat, lon, elevation_m)
    partial = (ghi > 0) & ((zenith_start >= 90) | (zenith_end >= 90))
    if partial.any():
        minutes = np.array(_SUB_HOUR_MINUTES, dtype=float)
        part_times = times[partial]
        up = np.stack(
            [_sun(part_times + pd.Timedelta(minutes=m), lat, lon, elevation_m)[0] < 90 for m in minutes]
        )
        n_up = up.sum(axis=0)
        centre = np.where(n_up > 0, (up * minutes[:, np.newaxis]).sum(axis=0) / np.maximum(n_up, 1), 30.0)
        zenith[partial], azimuth[partial] = _sun(
            part_times + pd.to_timedelta(centre, unit="min"), lat, lon, elevation_m
        )
    # light recorded with the sun below the horizon for the whole hour is all sky light
    zenith = np.where((ghi > 0) & (zenith >= 90), _MAX_DAYLIGHT_ZENITH, zenith)

    cos_zenith = np.cos(np.radians(zenith))
    sun_up = zenith < _MAX_DAYLIGHT_ZENITH
    dni = np.where(sun_up, (ghi - dhi) / np.maximum(cos_zenith, _MIN_COS_ZENITH), 0.0)
    dni = np.where(ghi > 0, np.minimum(dni, dni_extra), 0.0)
    dhi = np.where(ghi > 0, ghi - dni * np.clip(cos_zenith, 0.0, None), 0.0)
    return pd.DataFrame(
        {
            "time_utc": times,
            "month": times.month.to_numpy(),
            "ghi": ghi,
            "dni": dni,
            "dhi": dhi,
            "temp_air": df["temp_air"].to_numpy(dtype=float),
            "wind_speed": np.clip(df["wind_speed"].to_numpy(dtype=float), 0.0, None),
            "zenith": zenith,
            "azimuth": azimuth,
            "dni_extra": dni_extra,
        }
    )


def make_weather(
    df: pd.DataFrame, lat: float, lon: float, elevation_m: float, optimum_tilt_deg: float
) -> Weather:
    """One district's weather for the engine: `derive_hourly`, keeping the daylight hours (ghi > 0)."""
    hourly = derive_hourly(df, lat, lon, elevation_m)
    day = hourly[hourly["ghi"] > 0]
    arrays = {name: day[name].to_numpy() for name in _WEATHER_ARRAYS}
    return Weather(
        **arrays, latitude=lat, longitude=lon, elevation_m=elevation_m, optimum_tilt_deg=optimum_tilt_deg
    )


def check_weather(weather: Weather) -> list[str]:
    """Problems with one district's weather; an empty list means it passed.

    Checks that direct and sky light add up to the total, that direct light is not above the extraterrestrial
    value, and that the sunlight is in step with the sun: at a low sun the sky is about as clear in the
    morning as in the afternoon, so a large difference means the two are out of step.
    """
    problems = []
    cos_zenith = np.cos(np.radians(weather.zenith))
    gap = np.abs(weather.dni * cos_zenith + weather.dhi - weather.ghi).max()
    if gap > 1.0:
        problems.append(f"direct and sky light do not add up to the total (largest gap {gap:.1f} W/m2)")
    excess = (weather.dni - weather.dni_extra).max()
    if excess > 0.2:
        problems.append(f"direct light exceeds the extraterrestrial value by {excess:.1f} W/m2")
    low_sun = (cos_zenith > _LOW_SUN_COS[0]) & (cos_zenith < _LOW_SUN_COS[1])
    clearness = weather.ghi / (weather.dni_extra * np.maximum(cos_zenith, 1e-3))
    morning = low_sun & (weather.azimuth < 180)
    afternoon = low_sun & (weather.azimuth >= 180)
    if morning.any() and afternoon.any():
        am, pm = np.median(clearness[morning]), np.median(clearness[afternoon])
        if not _AM_PM_CLEARNESS_RATIO[0] <= am / max(pm, 1e-9) <= _AM_PM_CLEARNESS_RATIO[1]:
            problems.append(
                f"low-sun clearness is {am:.2f} in the morning and {pm:.2f} in the afternoon: "
                "the sunlight looks out of step with the sun"
            )
    return problems


def _rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def build_all(research_dir: Path, out_dir: Path) -> list[dict]:
    """Write a pack for every district with status 'ok', plus index.json. Returns the index entries."""
    tmy = research_dir / "08_solar_weather" / "tmy"
    tilt = {r["file"]: r for r in _rows(tmy / "tmy_opt_tilt.csv")}
    target = {r["file"].replace(".csv.gz", ""): r for r in _rows(tmy / "tmy_calibration.csv")}
    wanted = [r for r in _rows(tmy / "tmy_index.csv") if r["status"] == "ok"]
    out_dir.mkdir(parents=True, exist_ok=True)
    entries, problems = [], []
    for i, r in enumerate(wanted, 1):
        stem = r["file"].replace(".json.gz", "")
        lat, lon, elev = float(r["lat"]), float(r["lon"]), float(r["elevation_m"])
        opt = tilt[stem]
        df = pd.read_csv(tmy / "raw" / "pvgis_tmy_calibrated" / f"{stem}.csv.gz")
        try:
            weather = make_weather(df, lat, lon, elev, float(opt["gsa_opt_tilt_deg"]))
        except ValueError as err:  # a value outside the physical ranges that Weather accepts
            problems.append(f"{stem}: {err}")
            continue
        meta = {
            "dist_lgd": r["dist_lgd"],
            "district": r["district"],
            "state": r["state"],
            "data_version": DATA_VERSION,
            "attribution": ATTRIBUTION,
        }
        path = out_dir / f"{stem}.npz"
        save_weather(weather, meta, path)
        stored = load_weather(path)
        problems += [f"{stem}: {problem}" for problem in check_weather(stored)]
        ghi, dhi = stored.ghi.sum() / 1000, stored.dhi.sum() / 1000
        for name, got, want, tolerance in (
            ("GHI", ghi, float(target[stem]["ghi_after_kwh_m2_yr"]), GHI_TOLERANCE),
            ("DHI", dhi, float(target[stem]["dhi_after_kwh_m2_yr"]), DHI_TOLERANCE),
        ):
            if abs(got - want) > max(tolerance * want, 1.0):
                problems.append(f"{stem}: annual {name} {got:.1f} against {want:.0f} kWh/m2")
        entries.append(
            {
                "dist_lgd": r["dist_lgd"],
                "district": r["district"],
                "state": r["state"],
                "file": f"{stem}.npz",
                "lat": lat,
                "lon": lon,
                "elevation_m": elev,
                "optimum_tilt_deg": float(opt["gsa_opt_tilt_deg"]),
                "opt_tilt_source": opt["opt_tilt_source"],
                "n_hours": int(stored.ghi.size),
                "ghi_kwh_m2_yr": round(float(ghi), 1),
                "dhi_kwh_m2_yr": round(float(dhi), 1),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
        if i % 100 == 0:
            print(i, "packs written", flush=True)
    n_packs = len(list(out_dir.glob("*.npz")))
    if n_packs != len(wanted):
        problems.append(f"{n_packs} pack files in {out_dir} for {len(wanted)} districts")
    index = {
        "data_version": DATA_VERSION,
        "pack_version": PACK_VERSION,
        "attribution": ATTRIBUTION,
        "districts": entries,
    }
    with (out_dir / "index.json").open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(index, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    if problems:
        raise RuntimeError("weather pack checks failed:\n" + "\n".join(problems))
    return entries


def main(research_dir: Path, out_dir: Path) -> None:
    entries = build_all(research_dir, out_dir)
    size_mb = sum(p.stat().st_size for p in out_dir.glob("*.npz")) / 1e6
    print(f"{len(entries)} packs in {out_dir}, {size_mb:.1f} MB")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
