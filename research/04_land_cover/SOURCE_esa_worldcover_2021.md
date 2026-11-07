# SOURCE: ESA WorldCover 10 m 2021 v200: cropland fraction, district cropland and cropland centroids

| Field | Value |
|---|---|
| Dataset ID | D06 (cropland mask used to weight D02, D04 and D05) |
| Publisher / owner | European Space Agency WorldCover consortium (VITO with Brockmann Consult, Gamma Remote Sensing, IIASA, Wageningen University) |
| Dataset name and version | ESA WorldCover 10 m 2021 **v200** (Sentinel-1 + Sentinel-2), class 40 = Cropland, class 10 = Tree cover |
| URL / access route | `https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_<N##E###>_Map.tif` (public, no sign-in; 3° × 3° tiles of 36,000 × 36,000 px, ≈ 100 MB each). Product page: https://esa-worldcover.org ; Zenodo DOI 10.5281/zenodo.7254221 |
| Accessed on (YYYY-MM-DD) | 2026-11-07 |
| Reference year(s) covered | 2021 |
| Spatial coverage | Every 3° tile touching an LGD district (66–99° E, 6–39° N) |
| Spatial unit or resolution | Source 10 m; aggregated here to the **share of 10 m pixels per 0.01° cell** (≈ 1.1 km; 120 × 120 source pixels) |
| Temporal resolution | Static (2021) |
| Licence | **CC BY 4.0**: "provided free of charge, without restriction of use" (WorldCover Product User Manual v2.0, §5.1) |
| OK for a public open-source app? | **OK** with attribution |
| Required attribution text | "© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium" |
| Citation | Zanaga, D. et al. (2022). ESA WorldCover 10 m 2021 v200. https://doi.org/10.5281/zenodo.7254221 |
| Files in this folder | Committed: `worldcover_2021_district_cropland.csv` (785 LGD districts). Git-ignored: `raw/worldcover_2021/india_cropland_frac_0.01deg.tif` (band 1 cropland fraction, band 2 tree fraction; EPSG:4326) and `raw/worldcover_2021/tiles_0.01deg/*.npz` (per-tile aggregates; the 10 m tiles themselves were deleted after processing) |
| Units and key column meanings | `district_km2_grid` (district area on the 0.01° grid), `cropland_km2`, `cropland_share_pct`, `tree_share_pct` (% of district area), `crop_centroid_lon` / `crop_centroid_lat` (cropland-area-weighted centre: use this, not the polygon centre, for point look-ups such as solar and climate), `centroid_fallback` (true = no cropland, so a point inside the polygon is used), `low_cropland_flag` (cropland < 5% of area) |
| Known caveats and gaps | (1) **Orchards and plantations count as tree cover, not cropland** (FAO LCCS rule): horticulture and hill districts are badly under-mapped (Kullu 0.2% cropland vs about 7% in official records; Shimla 0.7%; Wayanad 3% with 90% tree cover). 126 districts carry `low_cropland_flag`; their cropland-weighted values rest on few cells. (2) One year only (2021) and no seasons: it cannot separate kharif-only from double-cropped land (that needs Dynamic World or Bhuvan LULC). (3) Fallow land often maps as grassland or bare, and greenhouses as built-up |
| Processing notes | `research/_scripts/worldcover_cropland_fraction.py` (curl download, strip-wise 120 × 120 block means, tile deleted after use; Python's urllib hit TLS resets on this host) and `research/_scripts/worldcover_district_cropland.py`. Run 2026-11-07: **all-India cropland 147.3 Mha**, against DES net sown area ≈ 140 Mha and NRSC's 2005-06 estimate of 142.6 Mha, so the totals are consistent. District median cropland share 49%. The same fraction grid weights `chirps_v3_…_cropland.csv`, `soilgrids_v2_…_cropland.csv` and `copdem_glo90_…_cropland.csv` |
