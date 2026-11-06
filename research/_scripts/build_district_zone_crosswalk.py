"""District × agro-zone area shares (15 Planning Commission ACZs, 20 NBSS&LUP AERs) keyed by LGD code.

Usage: uv run --no-project --with geopandas --with pyarrow python -I build_district_zone_crosswalk.py <research_dir>

Inputs (Bharatlas downloads, git-ignored):
  00_admin_boundaries/raw/bharatlas/LGD_Districts.parquet          (785 districts, dist_lgd)
  01_agro_climate/zones/raw/bharatlas/Agro_Climatic_Zones.parquet   (15 regions, regioncode)
  01_agro_climate/zones/raw/bharatlas/Agro_Ecological_Zones.parquet (20 regions, ae_regcode)
Outputs (committed):
  01_agro_climate/zones/district_zone_shares.csv   one row per district × zone with area_share >= 0.01
  01_agro_climate/zones/district_zone_primary.csv  one row per district: primary zone per scheme
Areas are computed in an equal-area projection (ESRI:102028, Asia South Albers). Shares below
SLIVER (5%) are flagged, not dropped, so downstream code can choose its own threshold.
"""

import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

EQUAL_AREA = "ESRI:102028"
SLIVER = 0.05


def load(path: Path) -> gpd.GeoDataFrame:
    g = gpd.read_parquet(path)
    if g.crs is None:
        g = g.set_crs(4326)
    g = g.to_crs(EQUAL_AREA)
    g["geometry"] = g.geometry.make_valid()
    return g


def shares(districts: gpd.GeoDataFrame, zones: gpd.GeoDataFrame, scheme: str, code: str, name: str) -> pd.DataFrame:
    z = zones[[code, name, "geometry"]].rename(columns={code: "zone_code", name: "zone_name"})
    inter = gpd.overlay(districts[["dist_lgd", "geometry"]], z, how="intersection", keep_geom_type=True)
    inter["area_km2"] = inter.geometry.area / 1e6
    out = inter.groupby(["dist_lgd", "zone_code", "zone_name"], as_index=False)["area_km2"].sum()
    out = out.merge(districts[["dist_lgd", "district_area_km2"]], on="dist_lgd")
    out["area_share"] = out["area_km2"] / out["district_area_km2"]
    out["scheme"] = scheme
    return out


def main(research: Path) -> None:
    zdir = research / "01_agro_climate" / "zones"
    d = load(research / "00_admin_boundaries" / "raw" / "bharatlas" / "LGD_Districts.parquet")
    d["district_area_km2"] = d.geometry.area / 1e6
    acz = load(zdir / "raw" / "bharatlas" / "Agro_Climatic_Zones.parquet")
    aer = load(zdir / "raw" / "bharatlas" / "Agro_Ecological_Zones.parquet")

    rows = pd.concat(
        [
            shares(d, acz, "acz15_planning_commission", "regioncode", "regionname"),
            shares(d, aer, "aer20_nbsslup_1992", "ae_regcode", "physio_reg"),
        ]
    )
    rows["zone_name"] = rows["zone_name"].str.replace("&amp;", "&").str.replace(r"\s+", " ", regex=True).str.strip()
    rows = rows.merge(d[["dist_lgd", "dtname", "state_lgd", "stname"]], on="dist_lgd")
    rows = rows[rows["area_share"] >= 0.01].copy()
    rows["is_sliver"] = rows["area_share"] < SLIVER
    rows["rank"] = rows.groupby(["dist_lgd", "scheme"])["area_share"].rank(ascending=False, method="first").astype(int)
    rows["is_primary"] = rows["rank"] == 1
    cols = ["dist_lgd", "dtname", "state_lgd", "stname", "scheme", "zone_code", "zone_name", "area_km2"]
    cols += ["area_share", "rank", "is_primary", "is_sliver"]
    rows = rows.sort_values(["state_lgd", "dist_lgd", "scheme", "rank"])[cols]
    rows["area_km2"] = rows["area_km2"].round(1)
    rows["area_share"] = rows["area_share"].round(4)
    rows.to_csv(zdir / "district_zone_shares.csv", index=False)

    prim = rows[rows["is_primary"]].pivot_table(
        index=["dist_lgd", "dtname", "state_lgd", "stname"],
        columns="scheme",
        values=["zone_code", "area_share"],
        aggfunc="first",
    )
    prim.columns = [f"{s}_{v}" for v, s in prim.columns]
    n_zones = rows[~rows["is_sliver"]].groupby(["dist_lgd", "scheme"]).size().unstack(fill_value=0)
    n_zones.columns = [f"{c}_n_zones_ge5pct" for c in n_zones.columns]
    prim = prim.reset_index().merge(n_zones.reset_index(), on="dist_lgd", how="left")
    all_d = d[["dist_lgd", "dtname", "state_lgd", "stname"]]
    prim = all_d.merge(prim, on=["dist_lgd", "dtname", "state_lgd", "stname"], how="left")
    prim.sort_values(["state_lgd", "dist_lgd"]).to_csv(zdir / "district_zone_primary.csv", index=False)
    print(len(rows), "district-zone rows;", len(prim), "districts")
    for s in rows["scheme"].unique():
        sub = rows[rows["scheme"] == s]
        covered = sub.groupby("dist_lgd")["area_share"].sum()
        print(
            s,
            "districts:",
            sub["dist_lgd"].nunique(),
            "| multi-zone (>=5%):",
            int((sub[~sub["is_sliver"]].groupby("dist_lgd").size() > 1).sum()),
            "| coverage<0.95:",
            int((covered < 0.95).sum()),
        )


if __name__ == "__main__":
    main(Path(sys.argv[1]))
