# SOURCE: INDIAN-SHAPEFILES (datta07), national district / state / sub-district GeoJSON

| Field | Value |
|---|---|
| Dataset ID | D00 |
| Publisher / owner | Akula Guru Datta and contributors (GitHub `datta07`) |
| Dataset name and version | INDIAN-SHAPEFILES, `master` branch as fetched on the access date (no tagged releases) |
| URL / access route | https://github.com/datta07/INDIAN-SHAPEFILES, files under `INDIA/`, fetched from `raw.githubusercontent.com/datta07/INDIAN-SHAPEFILES/master/...` |
| Accessed on (YYYY-MM-DD) | 2026-11-06 |
| Reference year(s) covered | README says "primarily 2019" boundaries with later updates. The district layer includes post-2019 districts (e.g. Alluri Sitharama Raju, Andhra Pradesh, created 2022) |
| Spatial coverage | All-India |
| Spatial unit or resolution | District polygons (820 features), state polygons (37), sub-district polygons (5,966) |
| Temporal resolution | One-off snapshot |
| Licence | MIT (repo `LICENSE`, copy saved as `raw/LICENSE`) |
| OK for a public open-source app? | OK as far as the licence goes. Before publishing, check the national outline against Survey of India's official depiction (D00 rule) |
| Required attribution text | "District boundaries: INDIAN-SHAPEFILES by Akula Guru Datta (MIT licence), github.com/datta07/INDIAN-SHAPEFILES" |
| Citation | Datta, A. G. (2022–). INDIAN-SHAPEFILES [GeoJSON]. GitHub. https://github.com/datta07/INDIAN-SHAPEFILES |
| Files in this folder | Git-ignored: `raw/INDIA_DISTRICTS.geojson` (77.8 MB), `raw/INDIA_STATES.geojson` (2.2 MB), `raw/INDIAN_SUB_DISTRICTS.geojson` (20.5 MB), `raw/LICENSE`. Committed: `datta07_districts_attributes.csv` (820 rows), `datta07_district_lgd_from_subdistricts.csv` (726 rows) |
| Units and key column meanings | Districts: `district`, `state`, `statecode`, `st_code`, `dist_code` (e.g. `555N002`, a source-specific code, **not LGD**), `D_CODE`, `remarks`. States: `STNAME`, `STCODE11` (Census 2011), `State_LGD`. Sub-districts: `stname`, `dtname`, `sdtname`, Census 2011 codes (`stcode11`, `dtcode11`, `sdtcode11`) and LGD codes (`State_LGD`, `Dist_LGD`, `Subdt_LGD`). CRS: WGS84 (EPSG:4326) |
| Known caveats and gaps | (1) The district layer has **no LGD code**, so it needs a name-to-LGD alias table. (2) It contains unnamed polygons flagged `DISPUTED (...)` in `remarks` (Rajasthan–Gujarat and Jharkhand–Bihar slivers). (3) The sub-district layer is Census-2011 era: it yields only 726 distinct districts, and some lack `Dist_LGD` (e.g. Mirpur). (4) The national outline may not match Survey of India's official depiction. (5) Boundaries may lag recent district changes |
| Processing notes | `research/_scripts/extract_datta07_attributes.py` writes the two committed CSVs (attributes only, no geometry; `bbox_centre_*` is a bounding-box centre, not a true centroid). Next D00 step: build `lgd_districts.csv` from the LGD directory and map the 820 polygons to LGD codes, using the sub-district LGD table as a bridge |
