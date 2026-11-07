"""District groundwater depth (pre- / post-monsoon, 2021-2025) from CGWB manual quarterly well readings on NWIC's
National Water Data Portal. Keyed by the LGD district code carried in each record.

Usage: python -I nwic_gwl_districts.py <research_dir>

1. Lists the "Ground Water Level (Manual - Quarterly)" dataset via the portal's CKAN API and downloads every
   2021-2025 state file to 05_groundwater_irrigation/cgwb_assessment/raw/nwic_gwl/ (resumable).
2. Seasons: pre-monsoon = April-June readings (May; June in some states), post-monsoon = October-December
   (November). Values must be numbers in 0-300 m below ground level; others are dropped.
3. Per well and season: median of the 2021-2025 readings (needs >= 2 readings). Per district: median across wells.
Writes 05_groundwater_irrigation/cgwb_assessment/nwic_gwl_district_depth_2021-2025.csv.
"""

import csv
import json
import statistics as st
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

API = "https://nwdp.nwic.gov.in/api/3/action/package_show?id=gwl-manual-quarterly-central-ground-water-board-department"
UA = {"User-Agent": "Mozilla/5.0 (agripv-lab-research)"}
PRE, POST = {4, 5, 6}, {10, 11, 12}
BANDS = [
    (2, "very shallow (0-2 m)"),
    (5, "shallow (2-5 m)"),
    (10, "moderate (5-10 m)"),
    (20, "moderately deep (10-20 m)"),
    (40, "deep (20-40 m)"),
    (float("inf"), "very deep (>40 m)"),
]


def get(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
        return r.read()


def band(v: float) -> str:
    return next(label for top, label in BANDS if v <= top)


def main(research: Path) -> None:
    folder = research / "05_groundwater_irrigation" / "cgwb_assessment"
    raw = folder / "raw" / "nwic_gwl"
    raw.mkdir(parents=True, exist_ok=True)
    res = json.loads(get(API))["result"]["resources"]
    files = []
    for r in res:
        if "2021_2025" not in r["url"]:
            continue
        p = raw / r["url"].rsplit("/", 1)[1]
        if not p.exists():
            p.write_bytes(get(r["url"]))
        files.append(p)
    print(len(files), "state files", flush=True)

    readings = defaultdict(lambda: {"pre": [], "post": []})
    meta = {}
    dropped = 0
    for p in files:
        with p.open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                try:
                    v = float(row["Groundwater Level Quarterly Manual (meter)"])
                    month = int(row["Data Acquisition Time"][3:5])
                    dist = int(row["District LGD Code"])
                except (ValueError, KeyError, TypeError):
                    dropped += 1
                    continue
                if not 0 <= v <= 300:
                    dropped += 1
                    continue
                season = "pre" if month in PRE else "post" if month in POST else None
                if season is None:
                    continue
                key = (dist, row["Station"], row["Latitude"], row["Longitude"])
                readings[key][season].append(v)
                meta[dist] = (row["District"], int(row["State LGD Code"] or 0), row["State"])

    per_dist = defaultdict(lambda: {"pre": [], "post": []})
    for (dist, *_), seasons in readings.items():
        for s, vals in seasons.items():
            if len(vals) >= 2:
                per_dist[dist][s].append(st.median(vals))

    out = folder / "nwic_gwl_district_depth_2021-2025.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "dist_lgd",
                "district",
                "state_lgd",
                "state",
                "n_wells_pre",
                "pre_monsoon_depth_m",
                "n_wells_post",
                "post_monsoon_depth_m",
                "seasonal_rise_m",
                "pre_monsoon_band",
            ]
        )
        for dist in sorted(per_dist, key=lambda d: (meta[d][1], d)):
            pre, post = per_dist[dist]["pre"], per_dist[dist]["post"]
            pm = round(st.median(pre), 2) if pre else ""
            qm = round(st.median(post), 2) if post else ""
            rise = round(pm - qm, 2) if pre and post else ""
            name, sl, sname = meta[dist]
            w.writerow([dist, name, sl, sname, len(pre), pm, len(post), qm, rise, band(pm) if pre else ""])
    print(len(per_dist), "districts;", len(readings), "wells;", dropped, "readings dropped ->", out)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
