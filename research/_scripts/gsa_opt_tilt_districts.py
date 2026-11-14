"""Global Solar Atlas optimum tilt at each district's typical-year point, for the weather packs.

Usage: uv run --no-project --with numpy python -I gsa_opt_tilt_districts.py <research_dir>

Reads 08_solar_weather/tmy/tmy_index.csv (the points the hourly weather was fetched for) and samples the
Atlas layer OPTA (optimum tilt of a fixed, equator-facing panel) with sample_gsa_districts.sample(), the mean
of cells within 0.04 degrees. Where the Atlas has no value at a point, the tilt falls back to the absolute
latitude and `opt_tilt_source` says so.
Writes 08_solar_weather/tmy/tmy_opt_tilt.csv; `file` is the district's file stem, e.g. 107_jodhpur.
"""

import csv
import math
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sample_gsa_districts import ZIP, sample


def main(research: Path) -> None:
    tmy = research / "08_solar_weather" / "tmy"
    with (tmy / "tmy_index.csv").open(encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r["status"] == "ok"]
    pts = [{"lat": float(r["lat"]), "lon": float(r["lon"])} for r in rows]
    with zipfile.ZipFile(research / "08_solar_weather" / "solar_atlas" / "raw" / "global_solar_atlas" / ZIP) as zf:
        opta = sample(zf, "OPTA", pts)[0]
    n_fallback = 0
    with (tmy / "tmy_opt_tilt.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["dist_lgd", "district", "file", "gsa_opt_tilt_deg", "opt_tilt_source"])
        for r, p, v in zip(rows, pts, opta, strict=True):
            ok = not math.isnan(v)
            n_fallback += not ok
            tilt = round(float(v), 1) if ok else round(abs(p["lat"]), 1)
            w.writerow([r["dist_lgd"], r["district"], r["file"].replace(".json.gz", ""), tilt,
                        "gsa" if ok else "latitude"])  # fmt: skip
    print(len(rows), "districts;", n_fallback, "used the latitude fallback")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
