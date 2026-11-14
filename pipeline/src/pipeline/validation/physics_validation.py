"""Check the physics engine against the Global Solar Atlas and PySAM at the reference districts (design spec §7).

Usage: python -m pipeline.validation.physics_validation <repo_root>

For each of the 10 reference districts in research/10_validation/energy_reference/energy_reference.csv, an
open-field monofacial plant at the Atlas's optimum tilt is simulated three ways:
- our engine (apv_physics), on the district's weather pack;
- Global Solar Atlas PV output (PVOUT), read from the reference table: must agree within 7%;
- PySAM's PVWatts v8, on the same calibrated hourly weather, tilt and losses: must agree within 3%.
Writes data/validation/physics_validation.csv and exits 1 if any district is outside a limit. The measured
plants are copied into the table for information only: their DC/AC ratios are not published.
"""

import csv
import json
import sys
from pathlib import Path

import pandas as pd
from apv_physics import MONOFACIAL, Kind, Layout, Losses, load_weather, simulate

GSA_LIMIT_PCT = 7.0
PYSAM_LIMIT_PCT = 3.0
OPEN_FIELD_ROW = 1  # GCR 0.05: rows far enough apart not to shade each other
COLUMNS = [
    "ref_id", "kind", "district", "tilt_deg", "engine_kwh_per_kwp", "gsa_pvout_kwh_per_kwp",
    "engine_vs_gsa_pct", "pysam_kwh_per_kwp", "engine_vs_pysam_pct", "pass_gsa", "pass_pysam", "note",
]  # fmt: skip


def _layout(tilt_deg: float) -> Layout:
    return Layout(
        Kind.FIXED, MONOFACIAL, height_m=1.0, collector_width_m=2.278, tilt_deg=tilt_deg, azimuth_deg=180.0
    )


def engine_annual(pack_path: Path, tilt_deg: float) -> float:
    """Annual kWh per kWp from our engine for an open-field monofacial plant at `tilt_deg`, facing south."""
    result = simulate(load_weather(pack_path), _layout(tilt_deg))
    return float(result.table.energy_kwh_per_kwp[OPEN_FIELD_ROW].sum())


def pysam_annual(
    csv_path: Path, lat: float, lon: float, elevation_m: float, tilt_deg: float, losses: Losses
) -> tuple[float, float]:
    """Annual kWh per kWp and annual plane-of-array irradiation (kWh/m2) from PySAM's PVWatts v8.

    The weather is the same calibrated hourly file the pack was built from. Time stamps are UTC (tz = 0) and
    `minute = 0` makes PySAM take the sun's position at the stamp, as the weather pack does.
    """
    import PySAM.Pvwattsv8 as pvwatts

    df = pd.read_csv(csv_path)
    t = pd.to_datetime(df["time_utc"], format="%Y%m%d:%H%M", utc=True)
    resource = {
        "lat": lat, "lon": lon, "tz": 0, "elev": elevation_m,
        "year": [2019] * len(df), "month": t.dt.month.tolist(), "day": t.dt.day.tolist(),
        "hour": t.dt.hour.tolist(), "minute": [0] * len(df),
        "dn": df["dni"].tolist(), "df": df["dhi"].tolist(), "gh": df["ghi"].tolist(),
        "tdry": df["temp_air"].tolist(), "wspd": df["wind_speed"].tolist(),
    }  # fmt: skip
    model = pvwatts.new()
    model.SolarResource.solar_resource_data = resource
    model.SystemDesign.system_capacity = 1000.0  # kW DC
    model.SystemDesign.module_type = 0  # standard
    model.SystemDesign.array_type = 0  # fixed, open rack
    model.SystemDesign.tilt = tilt_deg
    model.SystemDesign.azimuth = 180.0
    model.SystemDesign.gcr = 0.05
    model.SystemDesign.dc_ac_ratio = losses.dc_ac_ratio
    model.SystemDesign.inv_eff = 100.0 * losses.inverter_efficiency
    model.SystemDesign.losses = 100.0 * (1.0 - losses.dc_factor * losses.ac_factor)
    model.SystemDesign.bifaciality = 0.0
    model.execute()
    return model.Outputs.ac_annual / 1000.0, sum(model.Outputs.poa) / 1000.0


def _rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def run(repo: Path, with_pysam: bool = True) -> list[dict]:
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
        tilt = float(r["gsa_opt_tilt_deg"])
        engine = engine_annual(weather_dir / entry["file"], tilt)
        row = {
            "ref_id": r["ref_id"], "kind": r["kind"], "district": r["district"], "tilt_deg": tilt,
            "engine_kwh_per_kwp": round(engine, 1), "gsa_pvout_kwh_per_kwp": round(gsa),
            "engine_vs_gsa_pct": round(100 * (engine / gsa - 1), 2),
            "note": r["climate_or_plant"],
        }  # fmt: skip
        row["pass_gsa"] = abs(row["engine_vs_gsa_pct"]) <= GSA_LIMIT_PCT
        if with_pysam:
            stem = entry["file"].replace(".npz", "")
            pysam, _ = pysam_annual(
                calibrated / f"{stem}.csv.gz", entry["lat"], entry["lon"], entry["elevation_m"], tilt, losses
            )
            row["pysam_kwh_per_kwp"] = round(pysam, 1)
            row["engine_vs_pysam_pct"] = round(100 * (engine / pysam - 1), 2)
            row["pass_pysam"] = abs(row["engine_vs_pysam_pct"]) <= PYSAM_LIMIT_PCT
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
    failed = []
    for r in rows:
        if r["kind"] != "district_reference":
            continue
        print(
            f"{r['ref_id']} {r['district']:<12} tilt {r['tilt_deg']:>4}  engine {r['engine_kwh_per_kwp']:>7}"
            f"  Atlas {r['gsa_pvout_kwh_per_kwp']:>5} ({r['engine_vs_gsa_pct']:+.2f}%)"
            f"  PySAM {r['pysam_kwh_per_kwp']:>7} ({r['engine_vs_pysam_pct']:+.2f}%)"
        )
        if not (r["pass_gsa"] and r["pass_pysam"]):
            failed.append(r["district"])
    print("written", path)
    if failed:
        print("OUTSIDE LIMITS:", ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
