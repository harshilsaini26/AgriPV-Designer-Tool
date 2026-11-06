# SOURCE: NASA POWER: district climatology 2001–2020 (solar, temperature, rainfall, humidity, wind)

| Field | Value |
|---|---|
| Dataset ID | D14 (solar seasonality), D02 (rainfall), D03 (temperature) |
| Publisher / owner | NASA Langley Research Center, Prediction Of Worldwide Energy Resources (POWER) project. Solar from CERES / FLASHFlux; meteorology from MERRA-2 |
| Dataset name and version | POWER API v2 `temporal/climatology/point`, community `AG`, custom period **2001-01 to 2020-12** |
| URL / access route | `https://power.larc.nasa.gov/api/temporal/climatology/point?parameters=ALLSKY_SFC_SW_DWN,ALLSKY_SFC_SW_DIFF,ALLSKY_KT,T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,WS2M&community=AG&longitude=<lon>&latitude=<lat>&start=2001&end=2020&format=JSON`, one request per district centroid at about 1 request/second |
| Accessed on (YYYY-MM-DD) | 2026-11-06 |
| Reference year(s) covered | 2001–2020 mean |
| Spatial coverage | All-India: one point per named district polygon (792) |
| Spatial unit or resolution | Native grids: solar 1° × 1°, meteorology 0.5° × 0.625°. Neighbouring small districts can share a cell |
| Temporal resolution | Monthly climatology plus annual (`ANN`) |
| Licence | NASA POWER data are free and open with no restrictions; requested acknowledgement below |
| OK for a public open-source app? | OK |
| Required attribution text | "These data were obtained from the NASA Langley Research Center (LaRC) POWER Project funded through the NASA Earth Science/Applied Science Program." |
| Citation | NASA LaRC POWER Project (2026). POWER API v2 climatology, 2001–2020. https://power.larc.nasa.gov/ |
| Files in this folder | Committed: `nasa_power_district_climatology_2001-2020.csv` (long format: one row per district × parameter). Point list committed in `00_admin_boundaries/datta07_district_points.csv`. Git-ignored: `raw/nasa_power/<objectid>.json` (raw API responses, one per district) |
| Units and key column meanings | `objectid`, `state`, `district` (datta07 keys), `lon`, `lat` (area-weighted centroid of the district's largest polygon part), `power_elev_m` (POWER grid-cell elevation), `parameter`, `units`, `JAN`…`DEC`, `ANN`. Parameters: `ALLSKY_SFC_SW_DWN` GHI MJ/m²/day (÷ 3.6 → kWh/m²/day); `ALLSKY_SFC_SW_DIFF` diffuse MJ/m²/day; `ALLSKY_KT` clearness index; `T2M` mean air temperature °C; `T2M_MAX` / `T2M_MIN` °C; `PRECTOTCORR` bias-corrected precipitation mm/day (× days in month → mm/month); `RH2M` %; `WS2M` m/s |
| Known caveats and gaps | (1) **In climatology mode `T2M_MAX` / `T2M_MIN` are the extreme daily max / min within each month (and the `ANN` value is the absolute extreme), not the mean daily max / min.** For heat-stress thresholds use them as extremes; for the mean diurnal range use the `daily` API or IMD data. (2) Coarse grid: use for seasonal shape and as a cross-check of the Global Solar Atlas, not for absolute PV yield. (3) MERRA-2 rainfall underestimates orographic peaks (Western Ghats, North-East), so prefer IMD gridded rainfall for D02. (4) The point is the centroid of the largest polygon part; for coastal or island districts it can fall in a cell dominated by sea |
| Processing notes | `research/_scripts/fetch_nasa_power_districts.py` (resumable: cached JSON per district; retries with back-off). Run 2026-11-06: 792/792 districts, 0 retries, 7,128 rows. Checks: annual GHI ÷ Global Solar Atlas GHI at the same points has a median of 1.00 (range 0.93–1.28; the largest gaps are in hill districts, where the 1° cell is coarse); annual rainfall 234–3,610 mm (median 1,077); sub-zero annual T2M only in Leh, Kargil and Lahaul & Spiti, as expected |
