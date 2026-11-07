"""District crop calendars (planting and maturity dates) from the GGCMI Phase 3 crop calendar (0.5°, CC BY 4.0).

Usage: uv run --no-project --with rasterio --with geopandas --with pyarrow --with numpy --with netCDF4 \
         python -I ggcmi_district_crop_calendar.py <research_dir>

1. Rasterises the LGD districts onto the WorldCover 0.01° cropland-fraction grid (row key, as in
   worldcover_district_cropland.py) and maps every 0.01° cell to its 0.5° GGCMI cell.
2. Per district, crop and system (irrigated / rainfed): planting and maturity day-of-year are cropland-weighted
   **circular** means (dates wrap around 31 Dec); season length is the weighted mean. A district with no cropland
   falls back to area weights. `date_spread` is 1 − the mean resultant length of the planting dates: 0 means
   every cell agrees, > 0.05 (about ±1 month) means the district spans different calendars.
3. `qa`: "ok" where GGCMI used Indian statistics or RiceAtlas, "ok_lower_confidence" for global sources
   (MIRCA2000 / SAGE), and crop-specific warnings from spot checks (see QA).
4. `data_source` is the weighted majority of GGCMI's own source code (7 = Indian agricultural statistics,
   4 = RiceAtlas, 1 = MIRCA2000, 2 = SAGE, 3 = Iizuka, 5 = Dimou et al., 6 = ChinCropPhen).
Rye and sugar beet are skipped (not Indian crops). Writes
06_crops/crop_calendar/ggcmi_phase3_district_crop_calendar.csv.
"""

import datetime as dt
import sys
from pathlib import Path

import geopandas as gpd
import netCDF4
import numpy as np
import rasterio
from rasterio import features

KM_PER_DEG = 111.32
CROPS = {
    "ri1": "rice (main season)",
    "ri2": "rice (second season)",
    "swh": "wheat (spring)",
    "wwh": "wheat (winter)",
    "mai": "maize",
    "mil": "millet (bajra)",
    "sor": "sorghum (jowar)",
    "bar": "barley",
    "bea": "beans / pulses",
    "pea": "peas / pulses",
    "soy": "soybean",
    "nut": "groundnut",
    "rap": "rapeseed and mustard",
    "sun": "sunflower",
    "cot": "cotton",
    "sgc": "sugarcane",
    "pot": "potato",
    "cas": "cassava (tapioca)",
}
# Spot checks against Indian practice (Ludhiana, Agra, Patna, Indore, Rajkot, Nashik, Jaipur, Thanjavur, Bardhaman)
QA = {
    "pot": "do_not_use: dates come from MIRCA2000/SAGE and put plains potato in Jun-Nov; Indian practice is Oct-Mar",
    "nut": "check: rainfed rows in MP / Gujarat / Maharashtra / Rajasthan give the rabi groundnut window (Oct-Feb); "
    "the main kharif crop is Jun-Oct",
    "cas": "check: no Indian source; tapioca is mostly perennial-like (8-10 months)",
    "sun": "check: no Indian source",
}
SOURCES = {1: "MIRCA2000", 2: "SAGE", 3: "Iizumi", 4: "RiceAtlas", 5: "Dimou", 6: "ChinCropPhen", 7: "IndiaAgStat"}


def mmdd(doy: float) -> str:
    return (dt.date(2001, 1, 1) + dt.timedelta(days=round(doy) % 365)).strftime("%m-%d")


def main(research: Path) -> None:
    folder = research / "06_crops" / "crop_calendar"
    nc_dir = folder / "raw" / "ggcmi_phase3"
    with rasterio.open(research / "04_land_cover" / "raw" / "worldcover_2021" / "india_cropland_frac_0.01deg.tif") as r:
        crop = np.nan_to_num(r.read(1), nan=0.0)
        t, shape = r.transform, (r.height, r.width)
    d = gpd.read_parquet(research / "00_admin_boundaries" / "raw" / "bharatlas" / "LGD_Districts.parquet")
    d = (d.set_crs(4326) if d.crs is None else d.to_crs(4326)).reset_index(drop=True)
    n = len(d)
    ids = features.rasterize(
        ((g, i + 1) for i, g in enumerate(d.geometry)), out_shape=shape, transform=t, fill=0, dtype="int32"
    )
    lat = t.f + (np.arange(shape[0]) + 0.5) * t.e
    lon = t.c + (np.arange(shape[1]) + 0.5) * t.a
    cell_km2 = (abs(t.a) * KM_PER_DEG) * (abs(t.e) * KM_PER_DEG) * np.cos(np.radians(lat))
    m = ids > 0
    rr, cc = np.nonzero(m)
    k = ids[m]
    w_area = cell_km2[rr]
    w_crop = w_area * crop[m]
    has_crop = np.bincount(k, w_crop, n + 1)[1:] > 0
    w = np.where(has_crop[k - 1], w_crop, w_area)
    wsum = np.bincount(k, w, n + 1)[1:]

    with netCDF4.Dataset(nc_dir / "ri1_ir_ggcmi_crop_calendar_phase3_v1.01.nc4") as f:
        glat, glon = f.variables["lat"][:], f.variables["lon"][:]
    gi = np.rint((glat[0] - lat[rr]) / (glat[0] - glat[1])).astype(int)
    gj = np.rint((lon[cc] - glon[0]) / (glon[1] - glon[0])).astype(int)
    assert abs(glat[gi[0]] - lat[rr[0]]) <= 0.25 and abs(glon[gj[0]] - lon[cc[0]]) <= 0.25

    rows = []
    for code, name in CROPS.items():
        for system in ("ir", "rf"):
            with netCDF4.Dataset(nc_dir / f"{code}_{system}_ggcmi_crop_calendar_phase3_v1.01.nc4") as f:
                pdoy = np.ma.filled(f.variables["planting_day"][:], np.nan)[gi, gj]
                mdoy = np.ma.filled(f.variables["maturity_day"][:], np.nan)[gi, gj]
                gsl = np.ma.filled(f.variables["growing_season_length"][:], np.nan)[gi, gj]
                src = np.ma.filled(f.variables["data_source_used"][:], 0)[gi, gj].astype(int)
            ok = np.isfinite(pdoy) & np.isfinite(mdoy) & (pdoy > 0) & (mdoy > 0)
            wk = np.where(ok, w, 0.0)
            wtot = np.bincount(k, wk, n + 1)[1:]
            out = {}
            for var, vals in (("p", pdoy), ("m", mdoy)):
                ang = 2 * np.pi * (np.nan_to_num(vals) - 1) / 365
                cs = np.bincount(k, wk * np.cos(ang), n + 1)[1:]
                sn = np.bincount(k, wk * np.sin(ang), n + 1)[1:]
                with np.errstate(invalid="ignore", divide="ignore"):
                    out[var] = (np.degrees(np.arctan2(sn, cs)) % 360) / 360 * 365 + 1
                    out[var + "R"] = np.hypot(cs, sn) / wtot
            with np.errstate(invalid="ignore", divide="ignore"):
                season = np.bincount(k, wk * np.nan_to_num(gsl), n + 1)[1:] / wtot
            src_w = np.zeros((n, 10))
            np.add.at(src_w, (k - 1, np.clip(src, 0, 9)), wk)
            for i in range(n):
                if wtot[i] <= 0:
                    continue
                rows.append(
                    [
                        d.at[i, "dist_lgd"],
                        d.at[i, "dtname"],
                        d.at[i, "state_lgd"],
                        d.at[i, "stname"],
                        code,
                        name,
                        "irrigated" if system == "ir" else "rainfed",
                        round(float(out["p"][i]), 1),
                        mmdd(out["p"][i] - 1),
                        round(float(out["m"][i]), 1),
                        mmdd(out["m"][i] - 1),
                        round(float(season[i])),
                        round(max(0.0, 1 - float(out["pR"][i])), 3),
                        SOURCES.get(int(src_w[i].argmax()), "unknown"),
                        not has_crop[i],
                        QA.get(code, "ok" if int(src_w[i].argmax()) in (4, 7) else "ok_lower_confidence"),
                    ]
                )

    rows.sort(key=lambda r: (r[2], r[0], r[1], list(CROPS).index(r[4]), r[6]))
    path = folder / "ggcmi_phase3_district_crop_calendar.csv"
    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(
            "dist_lgd,district,state_lgd,state,ggcmi_crop,crop,system,planting_doy,planting_mmdd,"
            "maturity_doy,maturity_mmdd,season_days,date_spread,data_source,area_weight_fallback,qa\n"
        )
        for r in rows:
            fh.write(",".join(f'"{x}"' if isinstance(x, str) and "," in x else str(x) for x in r) + "\n")
    print(len(rows), "rows;", n, "districts;", int((wsum == 0).sum()), "without grid cells ->", path)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
