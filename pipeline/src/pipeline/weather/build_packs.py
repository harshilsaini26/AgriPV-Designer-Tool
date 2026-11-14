"""Build one weather pack per district from the calibrated hourly typical-year files (design spec §6).

Usage: python -m pipeline.weather.build_packs <research_dir> <out_dir>

Inputs, all under <research_dir>/08_solar_weather/tmy/:
- tmy_index.csv              district codes, point, elevation and file names
- tmy_opt_tilt.csv           Global Solar Atlas optimum tilt at each point (research/_scripts/gsa_opt_tilt_districts.py)
- tmy_calibration.csv        annual GHI and DHI after calibration, used to check each pack
- raw/pvgis_tmy_calibrated/  one hourly file per district (local, git-ignored)

Each pack holds the daylight hours only, with the sun's position at every hour computed here with pvlib, so
the live engine (apv_physics) needs no solar-position code.
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

DATA_VERSION = "2026-11-14"
ATTRIBUTION = (
    "Typical-year weather: PVGIS © European Union (JRC), PVGIS-ERA5 2005–2023; contains modified Copernicus "
    "Climate Change Service information (ERA5); calibrated to Global Solar Atlas 2.0 (Solargis / World Bank "
    "Group, CC BY 4.0)"
)


def make_weather(
    df: pd.DataFrame, lat: float, lon: float, elevation_m: float, optimum_tilt_deg: float
) -> Weather:
    """Add sun positions to one district's hourly table and keep the daylight hours (ghi > 0)."""
    times = pd.DatetimeIndex(pd.to_datetime(df["time_utc"], format="%Y%m%d:%H%M", utc=True))
    sun = pvlib.solarposition.get_solarposition(times, lat, lon, altitude=elevation_m)
    dni_extra = np.asarray(pvlib.irradiance.get_extra_radiation(times))
    keep = df["ghi"].to_numpy() > 0
    return Weather(
        month=times.month.to_numpy()[keep],
        ghi=df["ghi"].to_numpy()[keep],
        dni=df["dni"].to_numpy()[keep],
        dhi=df["dhi"].to_numpy()[keep],
        temp_air=df["temp_air"].to_numpy()[keep],
        wind_speed=df["wind_speed"].to_numpy()[keep],
        zenith=sun["apparent_zenith"].to_numpy()[keep],
        azimuth=sun["azimuth"].to_numpy()[keep],
        dni_extra=dni_extra[keep],
        latitude=lat,
        longitude=lon,
        elevation_m=elevation_m,
        optimum_tilt_deg=optimum_tilt_deg,
    )


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
        weather = make_weather(df, lat, lon, elev, float(opt["gsa_opt_tilt_deg"]))
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
        ghi, dhi = stored.ghi.sum() / 1000, stored.dhi.sum() / 1000
        for name, got, want in (
            ("GHI", ghi, float(target[stem]["ghi_after_kwh_m2_yr"])),
            ("DHI", dhi, float(target[stem]["dhi_after_kwh_m2_yr"])),
        ):
            if abs(got - want) > max(0.001 * want, 1.0):
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
