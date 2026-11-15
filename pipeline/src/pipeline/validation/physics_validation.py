"""Check the physics engine against the Global Solar Atlas and PySAM at the reference districts (design spec §7).

Usage: python -m pipeline.validation.physics_validation <repo_root>

For each of the 10 reference districts in research/10_validation/energy_reference/energy_reference.csv, an
open-field monofacial plant is simulated by our engine (apv_physics) on the district's weather pack and compared
with:
- Global Solar Atlas PV output (PVOUT), for a south-facing plant at the Atlas's optimum tilt: within 7%;
- PySAM's PVWatts v8 on the same hourly weather, tilt and losses, for the same south-facing plant: within 3%;
- PySAM again for plants facing due east and due west at 25 degrees: within 3%. South-facing plants cannot
  show an error in the timing of the sun; these two can.
Writes data/validation/physics_validation.csv and exits 1 if any district is outside a limit. The measured
plants are copied into the table for information only: their DC/AC ratios are not published.
"""

import csv
import json
import sys
from pathlib import Path

import pandas as pd
from apv_physics import MONOFACIAL, Kind, Layout, Losses, load_weather, simulate

from pipeline.weather.build_packs import derive_hourly

GSA_LIMIT_PCT = 7.0
PYSAM_LIMIT_PCT = 3.0
N_REFERENCE_DISTRICTS = 10
OPEN_FIELD_ROW = 1  # GCR 0.05: rows far enough apart not to shade each other
EAST_WEST_TILT_DEG = 25.0
COLUMNS = [
    "ref_id", "kind", "district", "tilt_deg", "engine_kwh_per_kwp", "gsa_pvout_kwh_per_kwp",
    "engine_vs_gsa_pct", "pysam_kwh_per_kwp", "engine_vs_pysam_pct",
    "engine_east_kwh_per_kwp", "pysam_east_kwh_per_kwp", "east_vs_pysam_pct",
    "engine_west_kwh_per_kwp", "pysam_west_kwh_per_kwp", "west_vs_pysam_pct",
    "pass_gsa", "pass_pysam", "pass_east_west", "note",
]  # fmt: skip


def engine_annual(pack_path: Path, tilt_deg: float, azimuth_deg: float = 180.0) -> float:
    """Annual kWh per kWp from our engine for an open-field monofacial plant."""
    layout = Layout(
        Kind.FIXED,
        MONOFACIAL,
        height_m=1.0,
        collector_width_m=2.278,
        tilt_deg=tilt_deg,
        azimuth_deg=azimuth_deg,
    )
    result = simulate(load_weather(pack_path), layout)
    return float(result.table.energy_kwh_per_kwp[OPEN_FIELD_ROW].sum())


def pysam_annual(hourly: pd.DataFrame, lat: float, lon: float, elevation_m: float, tilt_deg: float,
                 azimuth_deg: float, losses: Losses) -> float:  # fmt: skip
    """Annual kWh per kWp from PySAM's PVWatts v8 for the same plant on the same weather.

    `hourly` is `derive_hourly` output for the whole year: the irradiance the weather pack holds. Time stamps
    are UTC (tz = 0) and `minute = 30` puts PySAM's sun at mid-hour, where the pack's sun is.
    """
    import PySAM.Pvwattsv8 as pvwatts

    t = hourly["time_utc"]
    resource = {
        "lat": lat, "lon": lon, "tz": 0, "elev": elevation_m,
        "year": [2019] * len(hourly), "month": t.dt.month.tolist(), "day": t.dt.day.tolist(),
        "hour": t.dt.hour.tolist(), "minute": [30] * len(hourly),
        "dn": hourly["dni"].tolist(), "df": hourly["dhi"].tolist(), "gh": hourly["ghi"].tolist(),
        "tdry": hourly["temp_air"].tolist(), "wspd": hourly["wind_speed"].tolist(),
    }  # fmt: skip
    model = pvwatts.new()
    model.SolarResource.solar_resource_data = resource
    model.SystemDesign.system_capacity = 1000.0  # kW DC
    model.SystemDesign.module_type = 0  # standard
    model.SystemDesign.array_type = 0  # fixed, open rack
    model.SystemDesign.tilt = tilt_deg
    model.SystemDesign.azimuth = azimuth_deg
    model.SystemDesign.gcr = 0.05
    model.SystemDesign.dc_ac_ratio = losses.dc_ac_ratio
    model.SystemDesign.inv_eff = 100.0 * losses.inverter_efficiency
    model.SystemDesign.losses = 100.0 * (1.0 - losses.dc_factor * losses.ac_factor)
    model.SystemDesign.bifaciality = 0.0
    model.execute()
    return model.Outputs.ac_annual / 1000.0


def _rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _pct(a: float, b: float) -> float:
    return round(100 * (a / b - 1), 2)


def run(repo: Path) -> list[dict]:
    research = repo / "research"
    weather_dir = repo / "data" / "weather"
    index = json.loads((weather_dir / "index.json").read_text(encoding="utf-8"))["districts"]
    packs = {(e["dist_lgd"], e["district"]): e for e in index}
    calibrated = research / "08_solar_weather" / "tmy" / "raw" / "pvgis_tmy_calibrated"
    losses = Losses()
    out = []
    for r in _rows(research / "10_validation" / "energy_reference" / "energy_reference.csv"):
        gsa = float(r["gsa_pvout_kwh_per_kwp_yr"])
        if r["kind"] != "district_reference":
            out.append(
                {
                    "ref_id": r["ref_id"],
                    "kind": r["kind"],
                    "district": r["district"],
                    "gsa_pvout_kwh_per_kwp": round(gsa),
                    "note": f"for information: measured {r['measured_kwh_per_kw_yr']} kWh per {r['measured_basis']}"
                    f" ({r['measured_vs_gsa']}); {r['climate_or_plant']}",
                }
            )
            continue
        entry = packs[(r["dist_lgd"], r["district"])]
        pack = weather_dir / entry["file"]
        lat, lon, elev = entry["lat"], entry["lon"], entry["elevation_m"]
        hourly = derive_hourly(
            pd.read_csv(calibrated / entry["file"].replace(".npz", ".csv.gz")), lat, lon, elev
        )
        tilt = float(r["gsa_opt_tilt_deg"])

        engine = engine_annual(pack, tilt)
        pysam = pysam_annual(hourly, lat, lon, elev, tilt, 180.0, losses)
        row = {
            "ref_id": r["ref_id"], "kind": r["kind"], "district": r["district"], "tilt_deg": tilt,
            "engine_kwh_per_kwp": round(engine, 1), "gsa_pvout_kwh_per_kwp": round(gsa),
            "engine_vs_gsa_pct": _pct(engine, gsa),
            "pysam_kwh_per_kwp": round(pysam, 1), "engine_vs_pysam_pct": _pct(engine, pysam),
            "note": r["climate_or_plant"],
        }  # fmt: skip
        for name, azimuth in (("east", 90.0), ("west", 270.0)):
            ours = engine_annual(pack, EAST_WEST_TILT_DEG, azimuth)
            theirs = pysam_annual(hourly, lat, lon, elev, EAST_WEST_TILT_DEG, azimuth, losses)
            row[f"engine_{name}_kwh_per_kwp"] = round(ours, 1)
            row[f"pysam_{name}_kwh_per_kwp"] = round(theirs, 1)
            row[f"{name}_vs_pysam_pct"] = _pct(ours, theirs)
        row["pass_gsa"] = abs(row["engine_vs_gsa_pct"]) <= GSA_LIMIT_PCT
        row["pass_pysam"] = abs(row["engine_vs_pysam_pct"]) <= PYSAM_LIMIT_PCT
        row["pass_east_west"] = (
            abs(row["east_vs_pysam_pct"]) <= PYSAM_LIMIT_PCT
            and abs(row["west_vs_pysam_pct"]) <= PYSAM_LIMIT_PCT
        )
        out.append(row)
    return out


def main(repo: Path) -> int:
    rows = run(repo)
    path = repo / "data" / "validation" / "physics_validation.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n", restval="")
        w.writeheader()
        w.writerows(rows)
    reference = [r for r in rows if r["kind"] == "district_reference"]
    failed = []
    for r in reference:
        print(
            f"{r['ref_id']} {r['district']:<11} tilt {r['tilt_deg']:>4}  engine {r['engine_kwh_per_kwp']:>7}"
            f"  Atlas {r['engine_vs_gsa_pct']:+.2f}%  PySAM {r['engine_vs_pysam_pct']:+.2f}%"
            f"  | east {r['engine_east_kwh_per_kwp']:>7} ({r['east_vs_pysam_pct']:+.2f}%)"
            f"  west {r['engine_west_kwh_per_kwp']:>7} ({r['west_vs_pysam_pct']:+.2f}%)"
        )
        if not (r["pass_gsa"] and r["pass_pysam"] and r["pass_east_west"]):
            failed.append(r["district"])
    print("written", path)
    if len(reference) != N_REFERENCE_DISTRICTS:
        print(f"expected {N_REFERENCE_DISTRICTS} reference districts, found {len(reference)}")
        return 1
    if failed:
        print("OUTSIDE LIMITS:", ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
