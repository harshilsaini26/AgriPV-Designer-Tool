"""Write geometry-free attribute tables from the datta07/INDIAN-SHAPEFILES GeoJSONs.

Usage: python -I extract_datta07_attributes.py <research_dir>
Reads  00_admin_boundaries/raw/{INDIA_DISTRICTS,INDIAN_SUB_DISTRICTS}.geojson
Writes 00_admin_boundaries/datta07_districts_attributes.csv
       00_admin_boundaries/datta07_district_lgd_from_subdistricts.csv
"""

import csv
import json
import sys
from pathlib import Path


def bbox_centre(geom):
    xs, ys = [], []

    def walk(c):
        if isinstance(c[0], (int, float)):
            xs.append(c[0])
            ys.append(c[1])
        else:
            for x in c:
                walk(x)

    walk(geom["coordinates"])
    return round((min(xs) + max(xs)) / 2, 4), round((min(ys) + max(ys)) / 2, 4)


def main(research: Path) -> None:
    base = research / "00_admin_boundaries"
    raw = base / "raw"

    d = json.loads((raw / "INDIA_DISTRICTS.geojson").read_text(encoding="utf-8"))
    cols = ["objectid", "state", "statecode", "st_code", "district", "dist_code", "D_CODE", "remarks"]
    with (base / "datta07_districts_attributes.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([*cols, "bbox_centre_lon", "bbox_centre_lat"])
        for ft in sorted(
            d["features"], key=lambda x: (x["properties"]["state"] or "", x["properties"]["district"] or "")
        ):
            p = ft["properties"]
            w.writerow([*(p.get(c) or "" for c in cols), *bbox_centre(ft["geometry"])])
    print("districts:", len(d["features"]))

    s = json.loads((raw / "INDIAN_SUB_DISTRICTS.geojson").read_text(encoding="utf-8"))
    rows = {}
    for ft in s["features"]:
        p = ft["properties"]
        key = (p["State_LGD"], p["Dist_LGD"])
        rows.setdefault(key, (p["State_LGD"], p["stname"], p["stcode11"], p["Dist_LGD"], p["dtname"], p["dtcode11"], 0))
        r = rows[key]
        rows[key] = (*r[:6], r[6] + 1)
    with (base / "datta07_district_lgd_from_subdistricts.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "state_lgd",
                "state_name",
                "state_census2011",
                "district_lgd",
                "district_name",
                "district_census2011",
                "n_subdistricts",
            ]
        )
        for k in sorted(rows, key=lambda k: (k[0] or 0, k[1] or 0)):
            w.writerow(rows[k])
    print("districts with LGD (from sub-districts):", len(rows))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
