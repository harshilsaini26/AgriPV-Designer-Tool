"""India cropland-fraction grid (0.01°) from ESA WorldCover 2021 v200, class 40 (Cropland).

Usage: uv run --no-project --with rasterio --with geopandas --with pyarrow --with numpy \
         python -I worldcover_cropland_fraction.py <research_dir>

For each 3° WorldCover tile that touches an LGD district: download it to a temp file, read it in strips,
compute the share of 10 m pixels that are class 40 within each 0.01° cell (120 × 120 pixels), then delete the
tile. Also stores the tree-cover share (class 10), used to flag orchard / plantation districts that WorldCover
cannot see as cropland. Resumable: finished tiles are cached as small .npz files.
Writes 04_land_cover/raw/worldcover_2021/india_cropland_frac_0.01deg.tif (band 1 cropland, band 2 tree).
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.windows import Window

URL = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{t}_Map.tif"
CELL = 0.01
PIX = 120  # 10 m pixels (1/12000°) per 0.01° cell
W, S, E, N = 66.0, 6.0, 99.0, 39.0  # India grid extent (multiple of the 3° tiles)
STRIP = 1200  # rows per read = 10 output rows


def tile_name(lat: int, lon: int) -> str:
    return f"N{lat:02d}E{lon:03d}"


def process(name: str, cache: Path) -> Path | None:
    out = cache / f"{name}.npz"
    if out.exists() or (cache / f"{name}.missing").exists():
        return out if out.exists() else None
    with tempfile.TemporaryDirectory() as td:
        tif = Path(td) / f"{name}.tif"
        # curl with retries: Python's urllib hit TLS connection resets on this host
        res = subprocess.run(
            [
                "curl",
                "-sSL",
                "--retry",
                "8",
                "--retry-all-errors",
                "--retry-delay",
                "10",
                "-A",
                "agripv-lab-research/0.1",
                "-o",
                str(tif),
                "-w",
                "%{http_code}",
                URL.format(t=name),
            ],
            capture_output=True,
            text=True,
        )
        code = res.stdout.strip()[-3:]
        if code in ("403", "404"):
            (cache / f"{name}.missing").touch()
            return None
        if res.returncode != 0 or code != "200":
            raise RuntimeError(f"download failed for {name}: {code} {res.stderr[:200]}")
        with rasterio.open(tif) as src:
            h, w = src.height, src.width  # 36000 x 36000
            crop = np.zeros((h // PIX, w // PIX), dtype="float32")
            tree = np.zeros_like(crop)
            for r0 in range(0, h, STRIP):
                a = src.read(1, window=Window(0, r0, w, STRIP))
                blk = a.reshape(STRIP // PIX, PIX, w // PIX, PIX)
                rr = slice(r0 // PIX, r0 // PIX + STRIP // PIX)
                crop[rr] = (blk == 40).mean(axis=(1, 3))
                tree[rr] = (blk == 10).mean(axis=(1, 3))
    np.savez_compressed(out, crop=crop, tree=tree)
    print("tile", name, "cropland mean", round(float(crop.mean()), 3), flush=True)
    return out


def main(research: Path) -> None:
    folder = research / "04_land_cover" / "raw" / "worldcover_2021"
    cache = folder / "tiles_0.01deg"
    cache.mkdir(parents=True, exist_ok=True)
    d = gpd.read_parquet(research / "00_admin_boundaries" / "raw" / "bharatlas" / "LGD_Districts.parquet")
    d = d.set_crs(4326) if d.crs is None else d.to_crs(4326)
    sidx = d.sindex
    rows, cols = round((N - S) / CELL), round((E - W) / CELL)
    crop = np.full((rows, cols), np.nan, dtype="float32")
    tree = np.full((rows, cols), np.nan, dtype="float32")
    for lat in range(int(S), int(N), 3):
        for lon in range(int(W), int(E), 3):
            if not list(sidx.intersection((lon, lat, lon + 3, lat + 3))):
                continue
            p = process(tile_name(lat, lon), cache)
            if p is None:
                continue
            z = np.load(p)
            r0 = round((N - (lat + 3)) / CELL)
            c0 = round((lon - W) / CELL)
            n = z["crop"].shape[0]
            crop[r0 : r0 + n, c0 : c0 + n] = z["crop"]
            tree[r0 : r0 + n, c0 : c0 + n] = z["tree"]
    prof = {
        "driver": "GTiff",
        "height": rows,
        "width": cols,
        "count": 2,
        "dtype": "float32",
        "crs": "EPSG:4326",
        "transform": from_origin(W, N, CELL, CELL),
        "nodata": np.nan,
        "compress": "deflate",
        "tiled": True,
    }
    out = folder / "india_cropland_frac_0.01deg.tif"
    with rasterio.open(out, "w", **prof) as dst:
        dst.write(crop, 1)
        dst.write(tree, 2)
        dst.set_band_description(1, "cropland_fraction_class40")
        dst.set_band_description(2, "tree_fraction_class10")
    print("wrote", out)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
