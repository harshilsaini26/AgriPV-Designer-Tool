"""District cropland area, share and cropland centroid from the WorldCover 0.01° fraction grid.

Usage: uv run --no-project --with rasterio --with geopandas --with pyarrow --with numpy \
         python -I worldcover_district_cropland.py <research_dir>

Rasterises the LGD districts onto the 0.01° grid (cell centres; a row key is used because two PoK polygons
share LGD code 0) and sums cos(latitude)-weighted cell areas per district.
Writes 04_land_cover/worldcover_2021_district_cropland.csv.
"""

import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio import features

KM_PER_DEG = 111.32


def main(research: Path) -> None:
    lc = research / "04_land_cover"
    with rasterio.open(lc / "raw" / "worldcover_2021" / "india_cropland_frac_0.01deg.tif") as r:
        crop = np.nan_to_num(r.read(1), nan=0.0)
        tree = np.nan_to_num(r.read(2), nan=0.0)
        t, shape = r.transform, (r.height, r.width)
    d = gpd.read_parquet(research / "00_admin_boundaries" / "raw" / "bharatlas" / "LGD_Districts.parquet")
    d = (d.set_crs(4326) if d.crs is None else d.to_crs(4326)).reset_index(drop=True)
    n = len(d)
    ids = features.rasterize(
        ((g, i + 1) for i, g in enumerate(d.geometry)), out_shape=shape, transform=t, fill=0, dtype="int32"
    )
    lat = t.f + (np.arange(shape[0]) + 0.5) * t.e
    lon = t.c + (np.arange(shape[1]) + 0.5) * t.a
    cell_km2 = np.broadcast_to(
        (abs(t.a) * KM_PER_DEG) * (abs(t.e) * KM_PER_DEG) * np.cos(np.radians(lat))[:, None], shape
    )
    lon2 = np.broadcast_to(lon[None, :], shape)
    lat2 = np.broadcast_to(lat[:, None], shape)
    m = ids > 0
    k = ids[m]
    area = np.bincount(k, cell_km2[m], n + 1)[1:]
    ca = cell_km2 * crop
    crop_km2 = np.bincount(k, ca[m], n + 1)[1:]
    tree_km2 = np.bincount(k, (cell_km2 * tree)[m], n + 1)[1:]
    cx = np.bincount(k, (ca * lon2)[m], n + 1)[1:]
    cy = np.bincount(k, (ca * lat2)[m], n + 1)[1:]
    gc = d.geometry.representative_point()

    out = d[["dist_lgd", "dtname", "state_lgd", "stname"]].copy()
    with np.errstate(invalid="ignore", divide="ignore"):
        out["district_km2_grid"] = area.round(1)
        out["cropland_km2"] = crop_km2.round(1)
        out["cropland_share_pct"] = (100 * crop_km2 / area).round(1)
        out["tree_share_pct"] = (100 * tree_km2 / area).round(1)
        has = crop_km2 > 0
        out["crop_centroid_lon"] = np.where(has, cx / crop_km2, gc.x).round(4)
        out["crop_centroid_lat"] = np.where(has, cy / crop_km2, gc.y).round(4)
    out["centroid_fallback"] = ~has
    out["low_cropland_flag"] = out["cropland_share_pct"].fillna(0) < 5
    out.sort_values(["state_lgd", "dist_lgd"]).to_csv(lc / "worldcover_2021_district_cropland.csv", index=False)
    print(n, "districts; no grid cells:", int((area == 0).sum()), "; no cropland:", int((~has).sum()))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
