# SOURCE: World Bank Climate Change Knowledge Portal (CCKP), ERA5 1991–2020 climatology by state (rainfall)

| Field | Value |
|---|---|
| Dataset ID | D02 |
| Publisher / owner | World Bank Group, Climate Change Knowledge Portal. Underlying data: ECMWF ERA5 reanalysis (Copernicus Climate Change Service) |
| Dataset name and version | CCKP API v1, collection `era5-x0.25`, product `climatology`, variable `pr`, monthly, 1991–2020 mean, historical, area mean per geocode |
| URL / access route | Country page: https://climateknowledgeportal.worldbank.org/country/india. API pattern: `https://cckpapi.worldbank.org/cckp/v1/era5-x0.25_climatology_pr_climatology_monthly_1991-2020_mean_historical_era5_x0.25_mean/<geocodes>?_format=json` |
| Accessed on (YYYY-MM-DD) | 2026-11-06 |
| Reference year(s) covered | 1991–2020 (30-year normal) |
| Spatial coverage | All-India plus 36 states/UTs (pre-2019 set; no Ladakh) |
| Spatial unit or resolution | State/UT means of a 0.25° grid. **Not district level** |
| Temporal resolution | Monthly climatology |
| Licence | **CC BY 4.0** (World Bank Data Catalog id 0065626, DOI 10.57966/128g-6s70, checked 2026-11-06). Underlying ERA5 is under the Copernicus licence |
| OK for a public open-source app? | OK with attribution |
| Required attribution text | "Climate data: World Bank Climate Change Knowledge Portal (ERA5, Copernicus Climate Change Service / ECMWF)" |
| Citation | World Bank Group (2026). Climate Change Knowledge Portal, India: ERA5 0.25° monthly climatology 1991–2020. https://climateknowledgeportal.worldbank.org/ |
| Files in this folder | Committed: `cckp_era5_state_climatology_1991-2020.csv` (432 rows). Git-ignored: `raw/cckp_era5_1991-2020_pr.json` |
| Units and key column meanings | `cckp_geocode`, `state_name`, `month` (1–12), `pr` mean monthly precipitation total (mm) |
| Known caveats and gaps | (1) State means are a fallback and a sanity check only. D02 needs district normals and seasonal totals from IMD gridded rainfall (0.25°, 1901–present) or the IMD district-wise rainfall statistics. (2) ERA5 under-represents orographic rainfall peaks (Western Ghats, North-East). (3) State set predates 2019 |
| Processing notes | Fetched by `research/_scripts/fetch_cckp_state_climatology.py`. See also `SOURCE_niti_iced_climate.md` in `01_agro_climate/` (reviewed, not used) |
