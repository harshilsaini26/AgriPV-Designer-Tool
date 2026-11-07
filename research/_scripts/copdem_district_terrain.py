"""District elevation and slope-class shares from Copernicus DEM GLO-90 (AWS open data), keyed by LGD code.

Usage: uv run --no-project --with rasterio --with geopandas --with pyarrow --with numpy \
         python -I copdem_district_terrain.py <research_dir>

For every 1° tile touching an LGD district (66-98 E, 6-38 N):
  * download the tile once to 03_elevation/raw/copdem_glo90/ (resumable; missing tiles = sea);
  * slope (degrees) with Horn's 3x3 kernel using the true ground spacing per row:
    dy = 3" of latitude in metres, dx = dy * cos(latitude), so no single -s scale factor is used;
  * rasterise the districts on the tile grid and accumulate per district (cos-latitude area weights):
    area, mean elevation, and area with slope < 2°, < 5° and < 8°.
Tile-edge pixels have no full 3x3 neighbourhood and are skipped for slope (< 0.4% of pixels).
Writes 03_elevation/copdem_glo90_district_terrain.csv (area-weighted). With --cropland it also writes
..._terrain_cropland.csv, weighting each pixel by the WorldCover cropland fraction of its 0.01° cell
(slope shares become "% of cropland"; districts without cropland fall back to area weights).
"""

import sys
import urllib.request
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio import features

URL = "https://copernicus-dem-90m.s3.amazonaws.com/{n}/{n}.tif"
NAME = "Copernicus_DSM_COG_30_N{lat:02d}_00_E{lon:03d}_00_DEM"
M_PER_DEG = 111_320.0
THRESH = (2.0, 5.0, 8.0)


def tile(raw: Path, lat: int, lon: int) -> Path | None:
    n = NAME.format(lat=lat, lon=lon)
    p = raw / f"{n}.tif"
    miss = raw / f"{n}.missing"
    if p.exists():
        return p
    if miss.exists():
        return None
    try:
        req = urllib.request.Request(URL.format(n=n), headers={"User-Agent": "agripv-lab-research/0.1"})
        with urllib.request.urlopen(req, timeout=120) as r:
            p.with_suffix(".part").write_bytes(r.read())
        p.with_suffix(".part").replace(p)
        return p
    except urllib.error.HTTPError as e:
        if e.code in (403, 404):
            miss.touch()
            return None
        raise


def horn_slope(z: np.ndarray, lat_rows: np.ndarray, res_deg: float) -> np.ndarray:
    dy = res_deg * M_PER_DEG
    dx = (dy * np.cos(np.radians(lat_rows)))[1:-1, None]
    a, b, c = z[:-2, :-2], z[:-2, 1:-1], z[:-2, 2:]
    d, f = z[1:-1, :-2], z[1:-1, 2:]
    g, h, i = z[2:, :-2], z[2:, 1:-1], z[2:, 2:]
    dzdx = ((c + 2 * f + i) - (a + 2 * d + g)) / (8 * dx)
    dzdy = ((g + 2 * h + i) - (a + 2 * b + c)) / (8 * dy)
    s = np.full(z.shape, np.nan, dtype="float32")
    s[1:-1, 1:-1] = np.degrees(np.arctan(np.hypot(dzdx, dzdy)))
    return s


def main(research: Path) -> None:
    folder = research / "03_elevation"
    raw = folder / "raw" / "copdem_glo90"
    raw.mkdir(parents=True, exist_ok=True)
    d = gpd.read_parquet(research / "00_admin_boundaries" / "raw" / "bharatlas" / "LGD_Districts.parquet")
    d = (d.set_crs(4326) if d.crs is None else d.to_crs(4326)).reset_index(drop=True)
    n = len(d)
    acc = {k: np.zeros(n + 1) for k in ["area", "elev", "slope_area", "lt2", "lt5", "lt8", "elev_min", "elev_max"]}
    acc["elev_min"][:] = np.inf
    acc["elev_max"][:] = -np.inf
    cropland = "--cropland" in sys.argv
    keys = ["area", "elev", "slope_area", "lt2", "lt5", "lt8"]
    acc_c = {k: np.zeros(n + 1) for k in keys}
    crop = crop_t = None
    if cropland:
        with rasterio.open(
            research / "04_land_cover" / "raw" / "worldcover_2021" / "india_cropland_frac_0.01deg.tif"
        ) as cr:
            crop, crop_t = np.nan_to_num(cr.read(1), nan=0.0), cr.transform
    sindex = d.sindex
    lats = range(6, 38)
    for lat in lats:
        for lon in range(66, 98):
            hits = list(sindex.intersection((lon, lat, lon + 1, lat + 1)))
            if not hits:
                continue
            p = tile(raw, lat, lon)
            if p is None:
                continue
            with rasterio.open(p) as r:
                z = r.read(1).astype("float32")
                if r.nodata is not None:
                    z[z == r.nodata] = np.nan
                t = r.transform
                rows = np.arange(r.height)
                lat_1d = t.f + (rows + 0.5) * t.e
                lat_rows = lat_1d[:, None] * np.ones((1, r.width))
            sub = d.iloc[hits]
            ids = features.rasterize(
                ((g, k + 1) for k, g in zip(hits, sub.geometry)), out_shape=z.shape, transform=t, fill=0, dtype="int32"
            )
            w = np.cos(np.radians(lat_rows)) * (abs(t.a) * abs(t.e)) * M_PER_DEG**2 / 1e6  # km² per pixel
            slope = horn_slope(z, lat_1d, abs(t.e))
            ok = (ids > 0) & np.isfinite(z)
            k = ids[ok]
            acc["area"] += np.bincount(k, w[ok], n + 1)
            acc["elev"] += np.bincount(k, (z * w)[ok], n + 1)
            np.minimum.at(acc["elev_min"], k, z[ok])
            np.maximum.at(acc["elev_max"], k, z[ok])
            oks = ok & np.isfinite(slope)
            ks, ws, ss = ids[oks], w[oks], slope[oks]
            acc["slope_area"] += np.bincount(ks, ws, n + 1)
            for th in THRESH:
                acc[f"lt{int(th)}"] += np.bincount(ks, ws * (ss < th), n + 1)
            if cropland:
                lon_1d = t.c + (np.arange(z.shape[1]) + 0.5) * t.a
                ri = np.clip(((crop_t.f - lat_1d) / abs(crop_t.e)).astype(int), 0, crop.shape[0] - 1)
                ci = np.clip(((lon_1d - crop_t.c) / crop_t.a).astype(int), 0, crop.shape[1] - 1)
                wc = w * crop[ri[:, None], ci[None, :]]
                acc_c["area"] += np.bincount(k, wc[ok], n + 1)
                acc_c["elev"] += np.bincount(k, (z * wc)[ok], n + 1)
                wcs = wc[oks]
                acc_c["slope_area"] += np.bincount(ks, wcs, n + 1)
                for th in THRESH:
                    acc_c[f"lt{int(th)}"] += np.bincount(ks, wcs * (ss < th), n + 1)
        print("lat band", lat, "done", flush=True)

    out = d[["dist_lgd", "dtname", "state_lgd", "stname"]].copy()
    a, sa = acc["area"][1:], acc["slope_area"][1:]
    with np.errstate(invalid="ignore", divide="ignore"):
        out["dem_area_km2"] = a.round(1)
        out["elev_mean_m"] = (acc["elev"][1:] / a).round(1)
        out["elev_min_m"] = np.where(np.isfinite(acc["elev_min"][1:]), acc["elev_min"][1:], np.nan).round(0)
        out["elev_max_m"] = np.where(np.isfinite(acc["elev_max"][1:]), acc["elev_max"][1:], np.nan).round(0)
        for th in THRESH:
            out[f"pct_area_slope_lt{int(th)}deg"] = (100 * acc[f"lt{int(th)}"][1:] / sa).round(1)
    out["weighting"] = "area"
    out.sort_values(["state_lgd", "dist_lgd"]).to_csv(folder / "copdem_glo90_district_terrain.csv", index=False)
    print(n, "districts; missing:", int(pd.isna(out["elev_mean_m"]).sum()))
    if cropland:
        oc = out.copy()
        ca, csa = acc_c["area"][1:], acc_c["slope_area"][1:]
        fb = ca <= 0
        with np.errstate(invalid="ignore", divide="ignore"):
            oc["cropland_km2"] = ca.round(1)
            oc["cropland_share_pct"] = (100 * ca / a).round(1)
            oc["elev_mean_m"] = np.where(fb, out["elev_mean_m"], (acc_c["elev"][1:] / ca).round(1))
            for th in THRESH:
                col = f"pct_area_slope_lt{int(th)}deg"
                oc[col] = np.where(fb, out[col], (100 * acc_c[f"lt{int(th)}"][1:] / csa).round(1))
        oc["cropland_fallback"] = fb
        oc["weighting"] = "cropland"
        oc.sort_values(["state_lgd", "dist_lgd"]).to_csv(
            folder / "copdem_glo90_district_terrain_cropland.csv", index=False
        )
        print("cropland version written; fallback districts:", int(fb.sum()))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
