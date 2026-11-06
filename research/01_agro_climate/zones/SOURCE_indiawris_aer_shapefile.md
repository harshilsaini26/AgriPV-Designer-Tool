# SOURCE: Agro-Ecological Regions of India, shapefile (India-WRIS / NWIC; ICAR-NBSS&LUP delineation)

| Field | Value |
|---|---|
| Dataset ID | D01 |
| Publisher / owner | Delineation: ICAR-NBSS&LUP (20 agro-ecological regions). GIS layer: National Water Informatics Centre (NWIC), India-WRIS geodatabase (`IndiaWRIS2018.gdb`, published via `geospatial.nwicwriter.ADMINFD_NWIC`) |
| Dataset name and version | `Agro_Ecological_regions` shapefile. ArcGIS metadata: field edits dated 2020-03-19, file created 2022-09-15 |
| URL / access route | Uploaded by the project owner through the GitHub web UI (commits `763df40`…`151ab57`, Nov 2026). Most likely downloaded from India-WRIS (https://indiawris.gov.in), the GIS layers download section; **record the exact page URL here** |
| Accessed on (YYYY-MM-DD) | ≤ 2026-11-06 (upload date); exact download date not recorded |
| Reference year(s) covered | NBSS&LUP 1990s delineation |
| Spatial coverage | All-India |
| Spatial unit or resolution | 20 polygons (one per region) |
| Temporal resolution | One-off |
| Licence | Not stated. Metadata credit reads "As per ICAR, New Delhi". India-WRIS data is generally free to view and download for non-commercial use; check the portal's terms |
| OK for a public open-source app? | **Unknown.** The files are already public in this repo (web upload). Before shipping the geometry in the app, confirm India-WRIS / ICAR terms; a derived district→region lookup is the safer option |
| Required attribution text | "Agro-ecological regions: ICAR-NBSS&LUP; GIS layer: India-WRIS (NWIC, Ministry of Jal Shakti)" |
| Citation | Sehgal, J. et al. (1992). Agro-Ecological Regions of India. NBSS&LUP Publ. 24. GIS layer: India-WRIS, National Water Informatics Centre |
| Files in this folder | `Agro-Ecological Regions/Agro_Ecological_regions.{shp,shx,dbf,prj,cpg,sbn,sbx,shp.xml}` (5.0 MB .shp; committed). `Agro-Ecological Regions/To Be Deleted`: a placeholder file from the upload; safe to delete |
| Units and key column meanings | `ae_regcode` region number **1–20** (standard NBSS&LUP numbering; use this for joins), `physio_reg` region name, `area_sqkm`, `shape_Leng` / `shape_Area` (m, m²). CRS: Lambert Conformal Conic, WGS84, lat0 24°N, lon0 80°E, standard parallels 12.472944°N / 35.172806°N, false easting/northing 4,000,000 m. This matches **EPSG:7755 (India NSF LCC)**, the same projection inferred for the Kaggle soil points |
| Known caveats and gaps | (1) Same 20 regions as the FAO GAEZ layer (`SOURCE_fao_gaez_aer_india.md`); prefer this one because it has the numeric code. (2) **`area_sqkm` disagrees with the geometry for several regions** (e.g. region 5: 5,614 km² vs `shape_Area` 169,686 km²), so recompute areas from geometry. (3) Name typos as in the FAO copy ("EGO-REGION", "PLATU"). (4) Only 20 regions; the 60 sub-regions (AESR) are still missing |
| Processing notes | None yet. Planned: reproject to EPSG:4326, intersect with D00 districts, compute each district's dominant `ae_regcode` and area shares |
