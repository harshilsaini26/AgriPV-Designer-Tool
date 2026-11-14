"""Hourly typical meteorological year (TMY) for every district from PVGIS (ERA5), checked against Global Solar Atlas.

Usage: uv run --no-project --with numpy python -I pvgis_tmy_districts.py <research_dir> [workers]

1. Points: the WorldCover cropland centroid of each LGD district polygon
   (04_land_cover/worldcover_2021_district_cropland.csv; districts without cropland use the polygon's
   representative point, as recorded there).
2. Fetch: PVGIS 5.3 TMY API (https://re.jrc.ec.europa.eu/api/v5_3/tmy, radiation PVGIS-ERA5 and meteorology ERA5,
   2005-2023, horizon shading from the PVGIS DEM). The API response is kept as one gzipped JSON per district in
   08_solar_weather/tmy/raw/pvgis_tmy/ (resumable; failures are listed, not fatal).
3. Summaries: tmy_index.csv (annual GHI / DNI / DHI, diffuse share, mean temperature, months selected) and
   tmy_monthly.csv (monthly irradiation, diffuse fraction, temperature).
4. Check: Global Solar Atlas long-term GHI sampled at the same points with sample_gsa_districts.sample();
   `ghi_vs_gsa_pct` = TMY annual GHI / (GSA daily GHI x 365) - 1, flagged when outside +/-5% (D14 done-when).
   `ghi_scale_to_gsa` is the factor that would make the TMY's annual GHI match GSA (applied, if at all, by the
   physics pipeline to GHI, DNI and DHI alike); `dhi_vs_gsa_pct` compares diffuse light the same way.
"""

import csv
import gzip
import json
import re
import sys
import time
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sample_gsa_districts import ZIP, sample

API = "https://re.jrc.ec.europa.eu/api/v5_3/tmy?lat={lat}&lon={lon}&outputformat=json"
UA = {"User-Agent": "agripv-lab-research/0.1 (+https://github.com/harshilsaini26/AgriPV-Designer-Tool)"}
COLS = [("G(h)", "ghi"), ("Gb(n)", "dni"), ("Gd(h)", "dhi"), ("T2m", "temp_air"), ("RH", "relative_humidity"),
        ("WS10m", "wind_speed"), ("WD10m", "wind_direction"), ("IR(h)", "longwave_down"), ("SP", "pressure")]  # fmt: skip


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def fetch(lat: float, lon: float, tries: int = 4) -> dict:
    for k in range(tries):
        try:
            req = urllib.request.Request(API.format(lat=round(lat, 4), lon=round(lon, 4)), headers=UA)
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:300]
            if e.code == 400:  # e.g. "Location over the sea" - retrying will not help
                raise RuntimeError(f"HTTP 400: {body}") from e
            err = f"HTTP {e.code}: {body}"
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as e:  # network hiccups
            err = repr(e)
        time.sleep(5 * (k + 1))
    raise RuntimeError(err)


def get_one(p: dict, out_dir: Path) -> tuple[dict, str]:
    path = out_dir / f"{p['dist_lgd']}_{slug(p['district'])}.json.gz"
    if not path.exists():
        try:
            d = fetch(p["lat"], p["lon"])
        except RuntimeError as e:
            return p, str(e)
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            json.dump(d, fh)
    return p, ""


def main(research: Path, workers: int = 4) -> None:
    out_dir = research / "08_solar_weather" / "tmy" / "raw" / "pvgis_tmy"
    out_dir.mkdir(parents=True, exist_ok=True)
    pts = []
    with (research / "04_land_cover" / "worldcover_2021_district_cropland.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if not r["crop_centroid_lat"]:
                continue
            pts.append({"dist_lgd": r["dist_lgd"], "district": r["dtname"], "state_lgd": r["state_lgd"],
                        "state": r["stname"], "lat": float(r["crop_centroid_lat"]),
                        "lon": float(r["crop_centroid_lon"]), "fallback": r["centroid_fallback"]})  # fmt: skip
    print(len(pts), "points", flush=True)
    failures = []
    with ThreadPoolExecutor(workers) as ex:
        for i, (p, err) in enumerate(ex.map(lambda q: get_one(q, out_dir), pts), 1):
            if err:
                failures.append((p, err))
            if i % 50 == 0:
                print(i, "done;", len(failures), "failed", flush=True)

    with zipfile.ZipFile(research / "08_solar_weather" / "solar_atlas" / "raw" / "global_solar_atlas" / ZIP) as zf:
        gsa = {k: sample(zf, k, pts)[0] for k in ("GHI", "DIF")}  # (values, cell counts)

    tmy = research / "08_solar_weather" / "tmy"
    idx_f = (tmy / "tmy_index.csv").open("w", newline="", encoding="utf-8")
    mon_f = (tmy / "tmy_monthly.csv").open("w", newline="", encoding="utf-8")
    idx, mon = csv.writer(idx_f, lineterminator="\n"), csv.writer(mon_f, lineterminator="\n")
    idx.writerow(["dist_lgd", "district", "state_lgd", "state", "lat", "lon", "centroid_fallback", "elevation_m",
                  "file", "radiation_db", "period", "months_selected", "ghi_kwh_m2_yr", "dni_kwh_m2_yr",
                  "dhi_kwh_m2_yr", "diffuse_fraction", "temp_air_mean_c", "gsa_ghi_kwh_m2_yr", "ghi_vs_gsa_pct",
                  "gsa_flag", "ghi_scale_to_gsa", "gsa_dhi_kwh_m2_yr", "dhi_vs_gsa_pct", "status"])  # fmt: skip
    mon.writerow(["dist_lgd", "district", "month", "ghi_kwh_m2", "dni_kwh_m2", "dhi_kwh_m2", "diffuse_fraction",
                  "temp_air_mean_c", "relative_humidity_mean_pct", "source_year"])  # fmt: skip
    failed = {(f[0]["dist_lgd"], f[0]["district"]): f[1] for f in failures}
    n_flag = 0
    for i, p in enumerate(pts):
        path = out_dir / f"{p['dist_lgd']}_{slug(p['district'])}.json.gz"
        g_gsa = gsa["GHI"][i] * 365 if gsa["GHI"][i] == gsa["GHI"][i] else None
        base = [p["dist_lgd"], p["district"], p["state_lgd"], p["state"], round(p["lat"], 4), round(p["lon"], 4),
                p["fallback"]]  # fmt: skip
        if (p["dist_lgd"], p["district"]) in failed:
            idx.writerow([*base, "", "", "", "", "", "", "", "", "", "", round(g_gsa) if g_gsa else "", "", "",
                          "", "", "", "failed: " + failed[(p["dist_lgd"], p["district"])][:120]])  # fmt: skip
            continue
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            d = json.load(fh)
        h = d["outputs"]["tmy_hourly"]
        ghi = sum(x["G(h)"] for x in h) / 1000
        dhi = sum(x["Gd(h)"] for x in h) / 1000
        dni = sum(x["Gb(n)"] for x in h) / 1000
        tmean = sum(x["T2m"] for x in h) / len(h)
        sel = {m["month"]: m["year"] for m in d["outputs"]["months_selected"]}
        md = d["inputs"]["meteo_data"]
        pct = round(100 * (ghi / g_gsa - 1), 1) if g_gsa else ""
        scale = round(g_gsa / ghi, 4) if g_gsa else ""
        d_gsa = gsa["DIF"][i] * 365 if gsa["DIF"][i] == gsa["DIF"][i] else None
        dpct = round(100 * (dhi / d_gsa - 1), 1) if d_gsa else ""
        flag = "" if pct == "" else ("outside_5pct" if abs(pct) > 5 else "ok")
        n_flag += flag == "outside_5pct"
        idx.writerow([*base, d["inputs"]["location"]["elevation"], path.name, md["radiation_db"],
                      f"{md['year_min']}-{md['year_max']}", " ".join(f"{m}:{sel[m]}" for m in sorted(sel)),
                      round(ghi), round(dni), round(dhi), round(dhi / ghi, 3), round(tmean, 1),
                      round(g_gsa) if g_gsa else "", pct, flag, scale, round(d_gsa) if d_gsa else "", dpct,
                      "ok"])  # fmt: skip
        for m in range(1, 13):
            hm = [x for x in h if int(x["time(UTC)"][4:6]) == m]
            g = sum(x["G(h)"] for x in hm) / 1000
            df = sum(x["Gd(h)"] for x in hm) / 1000
            mon.writerow([p["dist_lgd"], p["district"], m, round(g, 1), round(sum(x["Gb(n)"] for x in hm) / 1000, 1),
                          round(df, 1), round(df / g, 3) if g else "", round(sum(x["T2m"] for x in hm) / len(hm), 1),
                          round(sum(x["RH"] for x in hm) / len(hm), 1), sel[m]])  # fmt: skip
    idx_f.close()
    mon_f.close()
    print(len(pts), "districts;", len(failures), "failed;", n_flag, "outside +/-5% of GSA")
    for p, err in failures:
        print("FAILED", p["dist_lgd"], p["district"], err[:150])


if __name__ == "__main__":
    main(Path(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 4)
