# SOURCE: India Soil Environment: Integrated Analysis (Kaggle, Lockhal), derived from ICAR-NBSS&LUP maps

| Field | Value |
|---|---|
| Dataset ID | D04 |
| Publisher / owner | Kaggle user "Lockhal" (compiler). Underlying thematic maps: ICAR National Bureau of Soil Survey & Land Use Planning (NBSS&LUP), https://nbsslup.icar.gov.in/ |
| Dataset name and version | `lockhal/india-soil-environment-integrated-analysis`, file `final_soil_environment_dataset_part.csv`, Kaggle "updated 4 months ago" as of the access date (≈ mid-2026) |
| URL / access route | https://www.kaggle.com/datasets/lockhal/india-soil-environment-integrated-analysis. Downloaded from `https://www.kaggle.com/api/v1/datasets/download/lockhal/india-soil-environment-integrated-analysis` (public, no sign-in needed) |
| Accessed on (YYYY-MM-DD) | 2026-11-06 |
| Reference year(s) covered | Not stated. The NBSS&LUP national maps date from the 1990s–2000s |
| Spatial coverage | All-India |
| Spatial unit or resolution | Points sampled from co-registered rasters: 105,506 points on a grid of roughly 2 km |
| Temporal resolution | One-off |
| Licence | Kaggle page states **CC BY 4.0** (as declared by the uploader). The upstream NBSS&LUP maps carry no stated open licence |
| OK for a public open-source app? | **Restricted until upstream terms are confirmed.** The CC BY label covers the compilation only, and the underlying ICAR data may not be redistributable. Use for research; ask NBSS&LUP before shipping derived layers |
| Required attribution text | "Soil depth, erosion, texture, slope and productivity classes: ICAR-NBSS&LUP, compiled by Lockhal (Kaggle, CC BY 4.0)" |
| Citation | Lockhal (2026). India Soil Environment: Integrated Analysis [dataset]. Kaggle. https://www.kaggle.com/datasets/lockhal/india-soil-environment-integrated-analysis |
| Files in this folder | Git-ignored: `raw/kaggle_lockhal/final_soil_environment_dataset_part.csv` (15.0 MB) |
| Units and key column meanings | `Longitude`, `Latitude`: **projected metres, not degrees** (x 2,817,631–5,553,067; y 2,255,559–5,437,287). The extent fits EPSG:7755 (India NSF LCC: lat0 24°N, lon0 80°E, false easting/northing 4,000,000 m); **this is inferred, so verify**. Coded classes with labels: `Depth` (4 classes, Extremely Shallow < 10 cm … Deep > 50 cm), `Erosion` (None to Slight … Very Severe Gullied), `Texture` (Fine / Medium / Coarse / Rocky and Non Soil), `Slope` (Nearly Level … Steep), `Productivity` (Non Productive … Highly Productive) |
| Known caveats and gaps | (1) The column names `Longitude`/`Latitude` are misleading because the values are projected; reproject before any join. (2) The CRS and source raster resolution are undocumented. (3) The file name says `_part`, so it may be a subset. (4) Classes are qualitative and have **no pH, organic carbon, available water capacity or bulk density**; those still need SoilGrids or NBSS&LUP / Soil Health Card data for D04. (5) "Productivity" is an NBSS&LUP land-productivity class, not crop yield |
| Processing notes | None yet. Planned: reproject (EPSG:7755 → 4326, after checking a few known points), spatially join to D00 district polygons, compute district class shares |
