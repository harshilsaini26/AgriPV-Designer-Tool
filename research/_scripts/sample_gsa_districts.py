"""Sample Global Solar Atlas (India, AAIGrid) layers around each district's centroid.

Usage: uv run --no-project --with numpy python -I sample_gsa_districts.py <research_dir>

Reads the India GIS zip in 08_solar_weather/solar_atlas/raw/global_solar_atlas/ without unpacking it,
streams each .asc grid, and averages valid cells within RADIUS_DEG of each point in
00_admin_boundaries/datta07_district_points.csv. On the 250 m grids every STRIDE-th row/column is used.
Writes 08_solar_weather/solar_atlas/gsa_district_centroid_stats.csv.

TEMP is skipped: the India TEMP.asc in this package is written with one significant digit ("3e+01").
NODATA cells (nan, or -9999 in OPTA) are excluded.
"""

import csv
import sys
import zipfile
from pathlib import Path

import numpy as np

ZIP = "India_GISdata_LTAym_AvgDailyTotals_GlobalSolarAtlas-v2_AAIGRID.zip"
PREFIX = "India_GISdata_LTAy_AvgDailyTotals_GlobalSolarAtlas-v2_AAIGRID/"
LAYERS = ["PVOUT", "GHI", "GTI", "DNI", "DIF", "OPTA"] + [f"monthly/PVOUT_{m:02d}" for m in range(1, 13)]
RADIUS_DEG = 0.04  # about 4.4 km


def sample(zf: zipfile.ZipFile, name: str, pts: list[dict]) -> list[float]:
    with zf.open(PREFIX + name + ".asc") as fh:
        head = {}
        for _ in range(6):
            k, v = fh.readline().decode().split()
            head[k.lower()] = float(v)
        ncols, nrows = int(head["ncols"]), int(head["nrows"])
        x0, y0, cs = head["xllcorner"], head["yllcorner"], head["cellsize"]
        nodata = head["nodata_value"]
        stride = 4 if cs < 0.005 else 1
        r = int(round(RADIUS_DEG / cs))
        need: dict[int, list[tuple[int, int, int]]] = {}
        for i, p in enumerate(pts):
            col = int((p["lon"] - x0) / cs)
            row = int((y0 + nrows * cs - p["lat"]) / cs)
            for rr in range(row - r, row + r + 1, stride):
                if 0 <= rr < nrows:
                    need.setdefault(rr, []).append((i, max(col - r, 0), min(col + r + 1, ncols)))
        sums = np.zeros(len(pts))
        counts = np.zeros(len(pts))
        for rr in range(nrows):
            line = fh.readline()
            if rr not in need:
                continue
            vals = np.array(line.split(), dtype=float)
            for i, c0, c1 in need[rr]:
                window = vals[c0:c1:stride]
                ok = window[np.isfinite(window) & (window != nodata)]
                sums[i] += ok.sum()
                counts[i] += ok.size
    with np.errstate(invalid="ignore", divide="ignore"):
        return list(np.where(counts > 0, sums / counts, np.nan)), list(counts)


def main(research: Path) -> None:
    pts_path = research / "00_admin_boundaries" / "datta07_district_points.csv"
    pts = [dict(r, lon=float(r["lon"]), lat=float(r["lat"])) for r in csv.DictReader(pts_path.open(encoding="utf-8"))]
    folder = research / "08_solar_weather" / "solar_atlas"
    results, n_cells = {}, None
    with zipfile.ZipFile(folder / "raw" / "global_solar_atlas" / ZIP) as zf:
        for layer in LAYERS:
            results[layer], counts = sample(zf, layer, pts)
            if layer == "PVOUT":
                n_cells = counts
            print("sampled", layer, flush=True)
    cols = [layer.replace("monthly/", "") for layer in LAYERS]
    with (folder / "gsa_district_centroid_stats.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["objectid", "state", "district", "lon", "lat", "pvout_cells", *cols])
        for i, p in enumerate(pts):
            vals = ["" if np.isnan(results[layer][i]) else round(results[layer][i], 3) for layer in LAYERS]
            w.writerow([p["objectid"], p["state"], p["district"], p["lon"], p["lat"], int(n_cells[i]), *vals])
    print("wrote", folder / "gsa_district_centroid_stats.csv")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
