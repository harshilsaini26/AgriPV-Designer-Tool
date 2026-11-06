# SOURCE: Global Solar Atlas 2.0: India GIS data (Solargis / World Bank ESMAP)

| Field | Value |
|---|---|
| Dataset ID | D14 (also the D18 energy reference) |
| Publisher / owner | The World Bank / ESMAP; data © Solargis (air temperature © ECMWF, NASA and Solargis) |
| Dataset name and version | `India_GISdata_LTAym_AvgDailyTotals_GlobalSolarAtlas-v2_AAIGRID.zip` (317,301,351 bytes; server timestamp 2019-10-22). Layer metadata dated 2019-10 (ISO 19115 PDF/XML inside the zip) |
| URL / access route | https://globalsolaratlas.info/download/india. File via `https://api.globalsolaratlas.info/download/India/<file name>` (redirects to a time-limited S3 link). The listing of files is at `https://api.globalsolaratlas.info/download/India?multilang=true` |
| Accessed on (YYYY-MM-DD) | 2026-11-06 |
| Reference year(s) covered | PVOUT long-term average 1999-2018 (solar layers similar; TEMP 1994-2018). The site notes country files were last updated in 2019, while the **World** layers were updated in 2026 (period to 2025): consider re-sampling from the World files later |
| Spatial coverage | India bounding box 66–98° E, 6–38° N |
| Spatial unit or resolution | GHI, GTI, DNI, DIF: 9 arcsec (≈ 250 m). PVOUT and monthly PVOUT: 30 arcsec (≈ 1 km). OPTA: 2 arcmin. EPSG:4326 |
| Temporal resolution | Long-term annual average of daily totals; monthly PVOUT |
| Licence | **CC BY 4.0**, with a binding addition that disputes go to WIPO mediation and then UNCITRAL arbitration (see the layer metadata and https://globalsolaratlas.info/support/terms-of-use) |
| OK for a public open-source app? | OK with attribution |
| Required attribution text | "Global Solar Atlas 2.0, a free, web-based application developed and operated by Solargis s.r.o. on behalf of the World Bank Group, utilizing Solargis data, with funding provided by ESMAP. https://globalsolaratlas.info" |
| Citation | World Bank Group, ESMAP & Solargis (2019). Global Solar Atlas 2.0, India GIS data (LTAym AvgDailyTotals). https://globalsolaratlas.info |
| Files in this folder | Committed: `gsa_district_centroid_stats.csv` (792 districts). Git-ignored: `raw/global_solar_atlas/India_GISdata_…_AAIGRID.zip` (317 MB; ≈ 3.5 GB unpacked, so it is read from the zip and never unpacked) |
| Units and key column meanings | `PVOUT` kWh/kWp/day: specific yield of a ground-mounted, fixed, optimally tilted, crystalline-Si PV system (× 365 for kWh/kWp/yr); `PVOUT_01`…`PVOUT_12` monthly kWh/kWp/day; `GHI` / `GTI` (at optimum tilt) / `DNI` / `DIF` kWh/m²/day; `OPTA` optimal tilt angle (°); `pvout_cells` cells averaged. Point key: `objectid`, `state`, `district`, `lon`, `lat` from `00_admin_boundaries/datta07_district_points.csv` |
| Known caveats and gaps | (1) **Window mean around the centroid (radius 0.04°, ≈ 4.4 km), not a district-wide mean**: fine for the indicative tool, but replace with zonal means once a raster tool chain exists. (2) **TEMP in the India package is unusable**: values are written with one significant digit ("3e+01"), so the column is dropped; use NASA POWER `T2M` or the GSA World TEMP layer instead. (3) OPTA uses −9999 for NODATA, which is excluded. (4) PVOUT assumes an open-field, optimally tilted plant: APV yields need the pvlib model with structure-specific tilt, height, GCR and bifacial gain; use PVOUT as the D18 reference and a sanity check (district median 4.19 kWh/kWp/day ≈ 1,531 kWh/kWp/yr; range 2.59–4.94) |
| Processing notes | `research/_scripts/sample_gsa_districts.py` (numpy; streams the zip). Checks: monthly PVOUT weighted by days in month reproduces annual PVOUT within ±0.1% for every district; GTI/GHI is 1.01–1.15; OPTA 8–35° |
