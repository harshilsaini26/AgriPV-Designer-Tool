"""Calibrate each district's PVGIS-ERA5 typical year to Global Solar Atlas annual GHI and diffuse (owner decision).

Usage: python -I calibrate_tmy_to_gsa.py <research_dir>

Inputs: 08_solar_weather/tmy/tmy_index.csv (GSA annual GHI and DHI at the same point) and the raw PVGIS responses
in 08_solar_weather/tmy/raw/pvgis_tmy/.

Method, hour by hour, keeping PVGIS's timing, temperature, humidity, wind and pressure:
1. GHI' = k_ghi x GHI, with k_ghi = GSA annual GHI / TMY annual GHI.
2. Beam' = c x k_ghi x (GHI - DHI) and DHI' = GHI' - beam', with one factor c per district chosen so that annual
   DHI' equals GSA annual DHI (closed form). ERA5's error is mostly missing aerosol in clear skies, so a fixed
   share of the direct beam becomes diffuse: clear hours shift most, overcast hours (little beam) barely move, and
   DHI' never exceeds GHI'. (A first version scaled DHI by a constant instead; it hit the GHI cap in about 1,100
   hours per district and gave implausible monsoon diffuse shares of 0.65-0.76.)
3. DNI' = DNI x beam' / beam: the horizontal beam is rescaled, so the hour's sun geometry is kept without
   recomputing solar position.
Outputs: raw/pvgis_tmy_calibrated/<file>.csv.gz (hourly), tmy_calibration.csv (factors and results per district),
tmy_monthly_calibrated.csv (monthly irradiation and diffuse fraction after calibration).
"""

import csv
import gzip
import json
import sys
from pathlib import Path

HOURLY_COLS = ["time_utc", "ghi", "dni", "dhi", "temp_air", "relative_humidity", "wind_speed", "wind_direction",
               "longwave_down", "pressure"]  # fmt: skip
MOUNTAIN_STATES = {"LADAKH"}


def calibrate(h: list[dict], g_target: float, d_target: float) -> tuple[list[tuple], float, float, int]:
    """Return calibrated hours, k_ghi, c_beam and the number of hours where the beam was capped at GHI'."""
    ghi = [x["G(h)"] for x in h]
    dhi = [x["Gd(h)"] for x in h]
    g_ann, d_ann = sum(ghi) / 1000, sum(dhi) / 1000
    k_g = g_target / g_ann
    # beam' = c x k_g x (GHI - DHI); annual DHI' = k_g x (G - c (G - D)) = target
    c = (g_ann - d_target / k_g) / (g_ann - d_ann)
    out, clipped = [], 0
    for x, g, d in zip(h, ghi, dhi):
        beam = max(g - d, 0.0)
        gn = k_g * g
        bn = c * k_g * beam
        if bn > gn:  # only possible when c > 1 (GSA diffuse below ERA5's)
            bn, clipped = gn, clipped + 1
        dn = gn - bn
        dni = x["Gb(n)"] * (bn / beam) if beam >= 1 else 0.0
        out.append((x["time(UTC)"], round(gn, 2), round(dni, 2), round(dn, 2), x["T2m"], x["RH"], x["WS10m"],
                    x["WD10m"], x["IR(h)"], x["SP"]))  # fmt: skip
    return out, k_g, c, clipped


def main(research: Path) -> None:
    tmy = research / "08_solar_weather" / "tmy"
    raw, out_dir = tmy / "raw" / "pvgis_tmy", tmy / "raw" / "pvgis_tmy_calibrated"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader((tmy / "tmy_index.csv").open(encoding="utf-8")))
    cal_f = (tmy / "tmy_calibration.csv").open("w", newline="", encoding="utf-8")
    mon_f = (tmy / "tmy_monthly_calibrated.csv").open("w", newline="", encoding="utf-8")
    cal, mon = csv.writer(cal_f, lineterminator="\n"), csv.writer(mon_f, lineterminator="\n")
    cal.writerow(["dist_lgd", "district", "state", "file", "k_ghi", "c_beam", "ghi_before_kwh_m2_yr",
                  "ghi_after_kwh_m2_yr", "dhi_before_kwh_m2_yr", "dhi_after_kwh_m2_yr", "dhi_target_kwh_m2_yr",
                  "dni_before_kwh_m2_yr", "dni_after_kwh_m2_yr", "diffuse_fraction_before", "diffuse_fraction_after",
                  "hours_beam_capped", "flag"])  # fmt: skip
    mon.writerow(["dist_lgd", "district", "month", "ghi_kwh_m2", "dni_kwh_m2", "dhi_kwh_m2", "diffuse_fraction"])
    done = 0
    for r in rows:
        if r["status"] != "ok" or not r["gsa_ghi_kwh_m2_yr"] or not r["gsa_dhi_kwh_m2_yr"]:
            cal.writerow([r["dist_lgd"], r["district"], r["state"], r["file"], *[""] * 12, "not_calibrated"])
            continue
        with gzip.open(raw / r["file"], "rt", encoding="utf-8") as fh:
            h = json.load(fh)["outputs"]["tmy_hourly"]
        out, k_g, c_b, capped = calibrate(h, float(r["gsa_ghi_kwh_m2_yr"]), float(r["gsa_dhi_kwh_m2_yr"]))
        name = r["file"].replace(".json.gz", ".csv.gz")
        with gzip.open(out_dir / name, "wt", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(HOURLY_COLS)
            w.writerows(out)
        g_a, d_a, b_a = (sum(o[i] for o in out) / 1000 for i in (1, 3, 2))
        flags = []
        if abs(k_g - 1) > 0.10:
            flags.append("ghi_scaled_over_10pct")
        if abs(d_a / float(r["gsa_dhi_kwh_m2_yr"]) - 1) > 0.01:
            flags.append("dhi_target_missed")
        if r["state"] in MOUNTAIN_STATES:
            flags.append("high_mountain_both_sources_uncertain")
        cal.writerow([r["dist_lgd"], r["district"], r["state"], name, round(k_g, 4), round(c_b, 4),
                      r["ghi_kwh_m2_yr"], round(g_a), r["dhi_kwh_m2_yr"], round(d_a), r["gsa_dhi_kwh_m2_yr"],
                      r["dni_kwh_m2_yr"], round(b_a), r["diffuse_fraction"], round(d_a / g_a, 3), capped,
                      ";".join(flags) or "ok"])  # fmt: skip
        for m in range(1, 13):
            om = [o for o in out if int(o[0][4:6]) == m]
            g = sum(o[1] for o in om) / 1000
            d = sum(o[3] for o in om) / 1000
            mon.writerow([r["dist_lgd"], r["district"], m, round(g, 1), round(sum(o[2] for o in om) / 1000, 1),
                          round(d, 1), round(d / g, 3) if g else ""])  # fmt: skip
        done += 1
    cal_f.close()
    mon_f.close()
    print(done, "districts calibrated of", len(rows))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
