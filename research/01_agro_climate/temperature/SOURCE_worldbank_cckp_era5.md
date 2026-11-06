# SOURCE: World Bank Climate Change Knowledge Portal (CCKP), ERA5 1991–2020 climatology by state (temperature)

| Field | Value |
|---|---|
| Dataset ID | D03 |
| Publisher / owner | World Bank Group, Climate Change Knowledge Portal. Underlying data: ECMWF ERA5 reanalysis (Copernicus Climate Change Service) |
| Dataset name and version | CCKP API v1, collection `era5-x0.25`, product `climatology`, monthly, 1991–2020 mean, historical, area mean per geocode |
| URL / access route | Country page: https://climateknowledgeportal.worldbank.org/country/india. API pattern: `https://cckpapi.worldbank.org/cckp/v1/era5-x0.25_climatology_<var>_climatology_monthly_1991-2020_mean_historical_era5_x0.25_mean/<geocodes>?_format=json`. State geocodes (`IND.1151` … `IND.11536`) come from the portal's `geonames.json` |
| Accessed on (YYYY-MM-DD) | 2026-11-06 |
| Reference year(s) covered | 1991–2020 (30-year normal) |
| Spatial coverage | All-India plus 36 states/UTs as CCKP defines them. This is the pre-2019 set: it has "Jammu and Kashmir", separate "Dadra and Nagar Haveli" and "Daman and Diu", and **no Ladakh** |
| Spatial unit or resolution | State/UT means of a 0.25° grid. **Not district level** |
| Temporal resolution | Monthly climatology (12 values per state) |
| Licence | Not stated on the CCKP pages checked (country page, About). World Bank data is generally CC BY 4.0, and ERA5 falls under the Copernicus licence (free, attribution required). **To confirm** |
| OK for a public open-source app? | Likely OK with attribution, but unconfirmed until the licence is checked |
| Required attribution text | "Climate data: World Bank Climate Change Knowledge Portal (ERA5, Copernicus Climate Change Service / ECMWF)" |
| Citation | World Bank Group (2026). Climate Change Knowledge Portal, India: ERA5 0.25° monthly climatology 1991–2020. https://climateknowledgeportal.worldbank.org/ ; Hersbach, H. et al. (2020). The ERA5 global reanalysis. QJRMS 146, 1999–2049 |
| Files in this folder | Committed: `cckp_era5_state_climatology_1991-2020.csv` (432 rows = 36 states + India × 12 months). Git-ignored: `raw/cckp_era5_1991-2020_{tas,tasmax,tasmin,hd35,hd40}.json` (API responses as received) |
| Units and key column meanings | `cckp_geocode` (`IND` = all-India), `state_name`, `month` (1–12), `tas` mean air temperature °C, `tasmax` mean daily maximum °C, `tasmin` mean daily minimum °C, `hd35` / `hd40` mean days per month with Tmax > 35 °C / > 40 °C |
| Known caveats and gaps | (1) State means hide large within-state gradients, so use them only as a **fallback and sanity check**. District values must come from IMD gridded data or ERA5-Land / AgERA5 (see `08_solar_weather/SOURCE_copernicus_cds.md`). (2) Reanalysis, not station data; ERA5 has known biases over the Himalaya. (3) State set predates 2019 |
| Processing notes | Fetched with `research/_scripts/fetch_cckp_state_climatology.py`. The API returns HTTP 403 to Python's default User-Agent, so the script sends a generic one. The same script writes the rainfall CSV (D02) |
