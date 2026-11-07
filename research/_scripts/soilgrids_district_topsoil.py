"""District topsoil (0-30 cm) properties from ISRIC SoilGrids 2.0 (1 km aggregated means), keyed by LGD code.

Usage: uv run --no-project --with rasterio --with geopandas --with pyarrow --with exactextract --with numpy \
         python -I soilgrids_district_topsoil.py <research_dir>

1. Clips the India window of each 1 km mean GeoTIFF (Goode Homolosine, ESRI:54052) over HTTP range requests
   into 02_soil/raw/soilgrids_v2_1km/<prop>_<depth>.tif (resumable).
2. Builds a 0-30 cm thickness-weighted layer per property: (5*d0_5 + 10*d5_15 + 15*d15_30) / 30, converted to
   conventional units.
3. Coverage-weighted district means with exactextract (area-weighted; cropland weighting comes later).
Writes 02_soil/soilgrids_v2_district_topsoil_0-30cm.csv.
"""

import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from exactextract import exact_extract
from rasterio.warp import Resampling, reproject, transform_bounds
from rasterio.windows import from_bounds

BASE = "/vsicurl/https://files.isric.org/soilgrids/latest/data_aggregated/1000m/{p}/{p}_{d}_mean_1000.tif"
DEPTHS = {"0-5cm": 5, "5-15cm": 10, "15-30cm": 15}
# property: (divide mapped integer by, output column, unit)
PROPS = {
    "clay": (10, "clay_pct", "%"),
    "silt": (10, "silt_pct", "%"),
    "sand": (10, "sand_pct", "%"),
    "phh2o": (10, "ph_h2o", "pH"),
    "soc": (10, "soc_g_per_kg", "g/kg"),
    "bdod": (100, "bulk_density_g_cm3", "g/cm3"),
    "cec": (10, "cec_cmolc_per_kg", "cmol(c)/kg"),
}
INDIA = (66.5, 6.0, 98.0, 38.0)
ENV = {
    "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
    "GDAL_HTTP_VERSION": "1.1",
    "GDAL_HTTP_TIMEOUT": "120",
    "GDAL_HTTP_MAX_RETRY": "5",
    "GDAL_HTTP_RETRY_DELAY": "5",
}


def clip(raw: Path, prop: str, depth: str) -> Path:
    out = raw / f"{prop}_{depth}.tif"
    if out.exists():
        return out
    with rasterio.Env(**ENV), rasterio.open(BASE.format(p=prop, d=depth)) as r:
        b = transform_bounds("EPSG:4326", r.crs, *INDIA, densify_pts=50)
        win = from_bounds(*b, r.transform).round_offsets().round_lengths()
        a = r.read(1, window=win)
        prof = r.profile | {
            "width": a.shape[1],
            "height": a.shape[0],
            "transform": r.window_transform(win),
            "compress": "deflate",
            "tiled": True,
            "blockxsize": 512,
            "blockysize": 512,
        }
        tmp = out.with_suffix(".part.tif")
        with rasterio.open(tmp, "w", **prof) as w:
            w.write(a, 1)
        tmp.replace(out)
    print("clipped", prop, depth, flush=True)
    return out


def topsoil(raw: Path, prop: str, factor: float) -> Path:
    out = raw / f"{prop}_0-30cm_weighted.tif"
    if out.exists():
        return out
    acc = None
    for depth, thick in DEPTHS.items():
        with rasterio.open(clip(raw, prop, depth)) as r:
            a = r.read(1).astype("float32")
            a[a == r.nodata] = np.nan
            prof = r.profile
        acc = a * thick if acc is None else acc + a * thick
    acc = acc / 30.0 / factor
    prof = prof | {"dtype": "float32", "nodata": np.nan}
    with rasterio.open(out, "w", **prof) as w:
        w.write(acc.astype("float32"), 1)
    return out


def cropland_weights(research: Path, raw: Path, template: Path) -> Path:
    """WorldCover cropland fraction (0.01°, EPSG:4326) averaged onto the 1 km soil grid."""
    out = raw / "cropland_frac_on_soil_grid.tif"
    if out.exists():
        return out
    src_path = research / "04_land_cover" / "raw" / "worldcover_2021" / "india_cropland_frac_0.01deg.tif"
    with rasterio.open(template) as t, rasterio.open(src_path) as s:
        dst = np.zeros((t.height, t.width), dtype="float32")
        reproject(
            np.nan_to_num(s.read(1), nan=0.0),
            dst,
            src_transform=s.transform,
            src_crs=s.crs,
            dst_transform=t.transform,
            dst_crs=t.crs,
            resampling=Resampling.average,
        )
        prof = t.profile | {"dtype": "float32", "nodata": None}
    with rasterio.open(out, "w", **prof) as w:
        w.write(dst, 1)
    return out


def main(research: Path) -> None:
    soil = research / "02_soil"
    raw = soil / "raw" / "soilgrids_v2_1km"
    raw.mkdir(parents=True, exist_ok=True)
    d = gpd.read_parquet(research / "00_admin_boundaries" / "raw" / "bharatlas" / "LGD_Districts.parquet")
    d = (d.set_crs(4326) if d.crs is None else d).reset_index(drop=True)
    d["row_id"] = d.index  # dist_lgd is not unique (two PoK polygons share code 0)
    result = d[["row_id", "dist_lgd", "dtname", "state_lgd", "stname"]].copy()
    cropland = "--cropland" in sys.argv
    wts = None
    for prop, (factor, col, _unit) in PROPS.items():
        path = topsoil(raw, prop, factor)
        with rasterio.open(path) as r:
            dd = d.to_crs(r.crs)
        if cropland:
            wts = wts or cropland_weights(research, raw, path)
            stats = exact_extract(
                str(path),
                dd[["row_id", "geometry"]],
                ["mean", "weighted_mean", "count", "weighted_sum"],
                weights=str(wts),
                include_cols=["row_id"],
                output="pandas",
            )
            fallback = ~np.isfinite(stats["weighted_mean"]) | (stats["weighted_sum"].abs() <= 0)
            stats["mean"] = np.where(fallback, stats["mean"], stats["weighted_mean"])
            if "cropland_fallback" not in result:
                result = result.merge(
                    stats[["row_id"]].assign(cropland_fallback=fallback.values), on="row_id", how="left"
                )
        else:
            stats = exact_extract(
                str(path), dd[["row_id", "geometry"]], ["mean", "count"], include_cols=["row_id"], output="pandas"
            )
        stats = stats.rename(columns={"mean": col, "count": f"{prop}_cells"})
        result = result.merge(stats[["row_id", col, f"{prop}_cells"]], on="row_id", how="left")
        print("district means", prop, flush=True)
    cols = [c for c in result.columns if not c.endswith("_cells") and c != "row_id"]
    result["n_cells_1km"] = result["clay_cells"].round(1)
    result = result[cols + ["n_cells_1km"]]
    for _, (_, col, _) in PROPS.items():
        result[col] = result[col].round(3 if "density" in col else 2)
    result["texture_sum_pct"] = (result["clay_pct"] + result["silt_pct"] + result["sand_pct"]).round(1)
    result["weighting"] = "cropland" if cropland else "area"
    name = "soilgrids_v2_district_topsoil_0-30cm" + ("_cropland" if cropland else "") + ".csv"
    result.sort_values(["state_lgd", "dist_lgd"]).to_csv(soil / name, index=False)
    print(len(result), "districts; missing clay:", int(result["clay_pct"].isna().sum()))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
