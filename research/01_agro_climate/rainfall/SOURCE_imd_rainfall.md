# SOURCE: IMD rainfall: district normals 1971–2020 (cross-check only) and gridded 0.25° data (not used)

| Field | Value |
|---|---|
| Dataset ID | D02 (validation / QA only) |
| Publisher / owner | India Meteorological Department (IMD), Climate Research and Services, Pune |
| Dataset name and version | (a) "All India Districtwise Rainfall Normals (1971–2020)", interactive qgis2web maps (annual, JJAS and monthly), from 4,132 gauges. (b) IMD 0.25° daily gridded rainfall (Pai et al. 2014), 1901–2025, `.grd` / NetCDF. **Not downloaded** |
| URL / access route | (a) https://www.imdpune.gov.in/climinfo/season/ann/index.html (annual) and …/season/mon/index.html (JJAS); district values sit in each map's layer file `layers/Rainfallinmm_1.js`. (b) https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html |
| Accessed on (YYYY-MM-DD) | 2026-11-06 |
| Reference year(s) covered | (a) 1971–2020 (50-year IMD normal, not the WMO 1991–2020 window). (b) 1901–2025 |
| Spatial coverage | All-India |
| Spatial unit or resolution | (a) 696 districts with values on the map (an older district set: simple mean of gauges in each district, not cropland-masked). (b) 0.25° |
| Temporal resolution | (a) Annual and seasonal normals. (b) Daily |
| Licence | No licence on the climinfo or gridded download pages (citation and disclaimer only). IMD's Data Supply Portal states: "Reproducing material published on this website for commercial purposes is prohibited unless written permission is obtained." IMD data e-books carry "All rights reserved" and no-third-party clauses |
| OK for a public open-source app? | **Restricted.** Keep local and use only to sanity-check our CHIRPS normals. Do not commit IMD values or ship them in the app without IMD's written permission |
| Required attribution text | (if ever cited) "India Meteorological Department, All India Districtwise Rainfall Normals (1971–2020)" |
| Citation | IMD (2022). District-wise rainfall normals 1971–2020 (press release 14 Apr 2022); Pai, D. S. et al. (2014). *Mausam* 65(1), 1–18 |
| Files in this folder | Git-ignored only: `raw/imd_district_normals_1971-2020/season_ann.js`, `season_mon.js` (GeoJSON layer files: `STATE`, `DISTRICT`, `Rainfall (in mm)`) |
| Units and key column meanings | mm (annual or JJAS normal) |
| Known caveats and gaps | 50-year window vs our 30-year one; gauge means are unmasked; older district names (needs fuzzy matching to LGD); some districts are flagged "Insufficient Data" |
| Processing notes | Used for the CHIRPS validation recorded in `SOURCE_chirps_v3.md`; no IMD values are committed |
