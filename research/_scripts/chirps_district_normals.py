"""District rainfall normals 1991-2020 from CHIRPS v3 monthly (0.05°), keyed by LGD district code.

Usage: uv run --no-project --with rasterio --with geopandas --with pyarrow --with numpy \
         python -I chirps_district_normals.py <research_dir>

1. Reads the India window (66.5-100.0 E, 6.5-38.5 N) of each monthly CHIRPS v3 COG over HTTP range requests
   and caches it per year in 01_agro_climate/rainfall/raw/chirps_v3/india_<year>.npz (resumable).
2. Weights each 0.05° cell by the fraction of it inside each LGD district (rasterised at 0.01°, i.e.
   25 sub-cells per cell) times cos(latitude). Area-weighted only: cropland weighting comes later.
3. Computes per-cell indicators first (needed for CV), then the weighted district mean.
Writes 01_agro_climate/rainfall/chirps_v3_district_rainfall_normals_1991-2020.csv.
"""

import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio import features
from rasterio.transform import from_origin
from rasterio.windows import from_bounds

URL = "/vsicurl/https://data.chc.ucsb.edu/products/CHIRPS/v3.0/monthly/global/cogs/chirps-v3.0.{y}.{m:02d}.cog"
W, S, E, N = 66.5, 6.5, 100.0, 38.5
RES = 0.05
SUB = 5  # sub-cells per side for coverage fractions
YEARS = range(1991, 2021)
SEASONS = {"jf": [1, 2], "mam": [3, 4, 5], "jjas": [6, 7, 8, 9], "ond": [10, 11, 12]}


def fetch(cache: Path) -> np.ndarray:
    cache.mkdir(parents=True, exist_ok=True)
    out = []
    env = {
        "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
        "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".cog",
        "GDAL_HTTP_MAX_RETRY": "5",
        "GDAL_HTTP_RETRY_DELAY": "5",
        "GDAL_HTTP_TIMEOUT": "60",
        "GDAL_HTTP_VERSION": "1.1",  # a background run hung on the default HTTP/2 path
    }
    with rasterio.Env(**env):
        for y in YEARS:
            f = cache / f"india_{y}.npz"
            if not f.exists():
                months = []
                for m in range(1, 13):
                    with rasterio.open(URL.format(y=y, m=m)) as r:
                        win = from_bounds(W, S, E, N, r.transform).round_offsets().round_lengths()
                        months.append(r.read(1, window=win))
                np.savez_compressed(f, rain=np.stack(months).astype("float32"))
                print("fetched", y, flush=True)
            out.append(np.load(f)["rain"])
    a = np.stack(out)  # (year, month, row, col)
    a[a < 0] = np.nan
    return a


def weights(districts: gpd.GeoDataFrame, shape: tuple[int, int]) -> tuple[np.ndarray, np.ndarray]:
    rows, cols = shape
    fine_t = from_origin(W, N, RES / SUB, RES / SUB)
    ids = features.rasterize(
        ((g, i + 1) for i, g in enumerate(districts.geometry)),
        out_shape=(rows * SUB, cols * SUB),
        transform=fine_t,
        fill=0,
        dtype="int32",
    )
    blocks = ids.reshape(rows, SUB, cols, SUB).transpose(0, 2, 1, 3).reshape(rows, cols, SUB * SUB)
    lat = N - (np.arange(rows) + 0.5) * RES
    coslat = np.cos(np.radians(lat))[:, None]
    wmat = np.zeros((len(districts), rows, cols), dtype="float32")
    for k in range(1, len(districts) + 1):
        frac = (blocks == k).mean(axis=2)
        wmat[k - 1] = frac * coslat
    return wmat, coslat


def main(research: Path) -> None:
    folder = research / "01_agro_climate" / "rainfall"
    rain = fetch(folder / "raw" / "chirps_v3")
    _, _, rows, cols = rain.shape
    d = gpd.read_parquet(research / "00_admin_boundaries" / "raw" / "bharatlas" / "LGD_Districts.parquet")
    d = d.to_crs(4326) if d.crs else d.set_crs(4326)
    wmat, _ = weights(d, (rows, cols))

    annual = rain.sum(axis=1)  # (year, row, col)
    per_cell = {f"m{m:02d}_mm": np.nanmean(rain[:, m - 1], axis=0) for m in range(1, 13)}
    per_cell["annual_mm"] = np.nanmean(annual, axis=0)
    for name, months in SEASONS.items():
        tot = rain[:, [m - 1 for m in months]].sum(axis=1)
        per_cell[f"{name}_mm"] = np.nanmean(tot, axis=0)
        if name in ("jjas", "ond"):
            per_cell[f"{name}_cv_pct"] = 100 * np.nanstd(tot, axis=0, ddof=1) / np.nanmean(tot, axis=0)
    per_cell["annual_cv_pct"] = 100 * np.nanstd(annual, axis=0, ddof=1) / np.nanmean(annual, axis=0)

    records = []
    for k, row in enumerate(d.itertuples()):
        w = wmat[k]
        rec = {"dist_lgd": row.dist_lgd, "district": row.dtname, "state_lgd": row.state_lgd, "state": row.stname}
        valid = np.isfinite(per_cell["annual_mm"]) & (w > 0)
        rec["n_cells"] = int((w > 0).sum())
        rec["coverage_frac"] = round(float(w[valid].sum() / w.sum()), 3) if w.sum() > 0 else 0.0
        for key, grid in per_cell.items():
            ok = valid & np.isfinite(grid)
            rec[key] = round(float((grid[ok] * w[ok]).sum() / w[ok].sum()), 1) if ok.any() else None
        records.append(rec)
    out = pd.DataFrame(records).sort_values(["state_lgd", "dist_lgd"])
    out["weighting"] = "area"
    out.to_csv(folder / "chirps_v3_district_rainfall_normals_1991-2020.csv", index=False)
    print(len(out), "districts written; missing:", int(out["annual_mm"].isna().sum()))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
