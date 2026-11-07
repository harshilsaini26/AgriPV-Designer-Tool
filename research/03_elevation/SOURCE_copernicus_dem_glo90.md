# SOURCE: Copernicus DEM GLO-90: district elevation and slope-class shares

| Field | Value |
|---|---|
| Dataset ID | D05 |
| Publisher / owner | European Space Agency / Copernicus programme. Data © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 (WorldDEM) |
| Dataset name and version | Copernicus DEM GLO-90 (`Copernicus_DSM_COG_30_*`, 3 arc-second Cloud-Optimized GeoTIFFs), AWS Open Data copy (objects dated 2022-05) |
| URL / access route | `https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_N<lat>_00_E<lon>_00_DEM/<same>.tif` (public, no sign-in; ≈ 5 MB per 1° tile). Licence linked from https://copernicus-dem-90m.s3.amazonaws.com/readme.html. The 30 m version (GLO-30) is in `copernicus-dem-30m` |
| Accessed on (YYYY-MM-DD) | 2026-11-07 |
| Reference year(s) covered | TanDEM-X acquisitions 2010–2015 |
| Spatial coverage | All 1° tiles touching an LGD district (66–98° E, 6–38° N) |
| Spatial unit or resolution | 3 arc-seconds (≈ 90 m); EPSG:4326, heights in metres above EGM2008 |
| Temporal resolution | Static |
| Licence | Copernicus DEM licence (GLO-30 Public / GLO-90): free of charge for the general public, worldwide, with attribution and a liability disclaimer |
| OK for a public open-source app? | **OK**, provided the attribution **and** the disclaimer below appear (put both in the app's data-sources footer) |
| Required attribution text | "Produced using Copernicus WorldDEM-90 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA; all rights reserved." **Disclaimer:** "The organisations in charge of the Copernicus programme by law or by delegation do not incur any liability for any use of the Copernicus WorldDEM-90." |
| Citation | European Space Agency (2024). Copernicus Global Digital Elevation Model. https://doi.org/10.5270/ESA-c5d3d65 |
| Files in this folder | Committed: `copdem_glo90_district_terrain.csv` (785 LGD districts). Git-ignored: `raw/copdem_glo90/*.tif` (1° tiles; `*.missing` marks all-sea tiles) |
| Units and key column meanings | `dem_area_km2` (district area covered by the DEM), `elev_mean_m`, `elev_min_m`, `elev_max_m` (m), `pct_area_slope_lt2deg`, `pct_area_slope_lt5deg`, `pct_area_slope_lt8deg` (% of district area with slope below 2°, 5° or 8°), `weighting` |
| Known caveats and gaps | (1) **Area-weighted, not cropland-weighted** yet: hill districts look steeper than their farmland. (2) It is a surface model (DSM): tree canopy and buildings create false slope at field edges. (3) 90 m smooths small terraces; GLO-30 would sharpen slope classes at ≈ 9× the data. (4) Pixels on 1° tile edges are skipped for slope (≈ 0.3%) |
| Processing notes | `research/_scripts/copdem_district_terrain.py`. Slope uses Horn's 3×3 kernel with **per-row ground spacing** (dy = 3″ of latitude in metres, dx = dy·cos(latitude)), avoiding the single `gdaldem -s 111120` scale factor, which biases slope with latitude. District sums use cos-latitude pixel areas. Run 2026-11-07: 383 land tiles (14 all-sea tiles marked `.missing`); 784/785 districts (**Sanchor** has an empty polygon, as in the CHIRPS table). Checks: DEM areas match official district areas (Ludhiana 3,702 vs 3,767 km²; Jaisalmer 38,601 vs 38,401; Bhopal 2,780 vs 2,772); slope shares are monotonic (< 2° ≤ < 5° ≤ < 8°) everywhere; plains vs hills behave as expected (Ludhiana 99% of area < 2°; Kullu 0.3%; Wayanad 9%). Negative minima are open-cast mines, not errors (Cuddalore −93 m at Neyveli lignite; Anugul, Bhadradri Kothagudem and Paschim Bardhaman coalfields). Leh's area (154,376 km²) and maximum (8,565 m) include territory claimed by India, following the LGD polygon |
