"""District climatology (2001-2020) from NASA POWER at each district polygon's centroid.

Usage: python -I fetch_nasa_power_districts.py <research_dir>

1. Computes an area-weighted centroid of each district's largest polygon part from
   00_admin_boundaries/raw/INDIA_DISTRICTS.geojson (datta07; unnamed "DISPUTED" slivers skipped)
   and writes 00_admin_boundaries/datta07_district_points.csv.
2. Calls the POWER climatology point API once per district (about 1 request per second),
   caching each response in 08_solar_weather/solar_atlas/raw/nasa_power/<objectid>.json (resumable).
3. Writes 08_solar_weather/solar_atlas/nasa_power_district_climatology_2001-2020.csv (long format).
"""

import csv
import json
import sys
import time
import urllib.request
from pathlib import Path

API = (
    "https://power.larc.nasa.gov/api/temporal/climatology/point?parameters={p}&community=AG"
    "&longitude={lon}&latitude={lat}&start=2001&end=2020&format=JSON"
)
PARAMS = "ALLSKY_SFC_SW_DWN,ALLSKY_SFC_SW_DIFF,ALLSKY_KT,T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,WS2M"
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC", "ANN"]


def ring_centroid(ring):
    a = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
        cross = x0 * y1 - x1 * y0
        a += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    if abs(a) < 1e-12:
        xs, ys = zip(*ring)
        return 0.0, sum(xs) / len(xs), sum(ys) / len(ys)
    return abs(a) / 2, cx / (3 * a), cy / (3 * a)


def centroid(geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    best = max((ring_centroid([tuple(p[:2]) for p in poly[0]]) for poly in polys), key=lambda t: t[0])
    return round(best[1], 4), round(best[2], 4)


def points(research: Path) -> list[dict]:
    src = research / "00_admin_boundaries" / "raw" / "INDIA_DISTRICTS.geojson"
    feats = json.loads(src.read_text(encoding="utf-8"))["features"]
    rows = []
    for f in feats:
        p = f["properties"]
        if not p.get("district"):
            continue
        lon, lat = centroid(f["geometry"])
        rows.append({"objectid": p["objectid"], "state": p["state"], "district": p["district"], "lon": lon, "lat": lat})
    rows.sort(key=lambda r: (r["state"], r["district"], r["objectid"]))
    out = research / "00_admin_boundaries" / "datta07_district_points.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return rows


def fetch(lon: float, lat: float) -> dict:
    req = urllib.request.Request(
        API.format(p=PARAMS, lon=lon, lat=lat), headers={"User-Agent": "agripv-lab-research/0.1"}
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def main(research: Path) -> None:
    pts = points(research)
    folder = research / "08_solar_weather" / "solar_atlas"
    cache = folder / "raw" / "nasa_power"
    cache.mkdir(parents=True, exist_ok=True)
    for i, p in enumerate(pts):
        path = cache / f"{p['objectid']}.json"
        if path.exists():
            continue
        for attempt in range(4):
            try:
                path.write_text(json.dumps(fetch(p["lon"], p["lat"])), encoding="utf-8")
                break
            except Exception as e:  # network hiccup or rate limit: back off and retry
                print("retry", p["district"], e, flush=True)
                time.sleep(10 * (attempt + 1))
        time.sleep(1.0)
        if i % 50 == 0:
            print(i, "/", len(pts), flush=True)

    out = folder / "nasa_power_district_climatology_2001-2020.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["objectid", "state", "district", "lon", "lat", "power_elev_m", "parameter", "units", *MONTHS])
        for p in pts:
            path = cache / f"{p['objectid']}.json"
            if not path.exists():
                continue
            d = json.loads(path.read_text(encoding="utf-8"))
            meta = d.get("parameters", {})
            elev = d["geometry"]["coordinates"][2] if len(d["geometry"]["coordinates"]) > 2 else ""
            for k, v in d["properties"]["parameter"].items():
                units = meta.get(k, {}).get("units", "")
                w.writerow(
                    [
                        p["objectid"],
                        p["state"],
                        p["district"],
                        p["lon"],
                        p["lat"],
                        elev,
                        k,
                        units,
                        *[v.get(m, "") for m in MONTHS],
                    ]
                )
    print("wrote", out)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
