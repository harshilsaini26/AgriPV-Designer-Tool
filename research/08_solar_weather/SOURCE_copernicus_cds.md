# SOURCE: Copernicus Climate Data Store (CDS): candidate datasets (not yet downloaded: needs your account)

| Field | Value |
|---|---|
| Dataset ID | D14 (solar, typical-year weather), D02 (rainfall), D03 (temperature), D15 (albedo) |
| Publisher / owner | Copernicus Climate Change Service (C3S), implemented by ECMWF on behalf of the European Commission |
| Dataset name and version | Shortlist (CDS catalogue, 144 datasets on the access date): **(1)** `reanalysis-era5-land-monthly-means` (0.1°, 1950–present: `2m_temperature`, `total_precipitation`, `surface_solar_radiation_downwards`); **(2)** `sis-agrometeorological-indicators` (AgERA5 v2.0, daily 0.1°, 1979–present: Tmax/Tmin/Tmean, solar radiation flux, precipitation, vapour pressure, wind; built for crop modelling); **(3)** `sis-agroclimatic-indicators` (10-day 0.5° indicators such as growing-season length and heat days, historical + CMIP projections); **(4)** `satellite-albedo` (C3S surface albedo, for D15). Also check `cams-solar-radiation-timeseries` on the sister Atmosphere Data Store (ADS): it gives hourly GHI/DNI/DHI per point, so confirm it covers India before relying on it |
| URL / access route | https://cds.climate.copernicus.eu/datasets. Access is by **CDS account + API key + one-time licence acceptance per dataset**, then the `cdsapi` client. Script: `research/_scripts/fetch_cds_india.py` (India bounding box N38 W68 S6 E98) |
| Accessed on (YYYY-MM-DD) | 2026-11-06 (catalogue reviewed; no data downloaded) |
| Reference year(s) covered | Planned: 1991–2020 normals (ERA5-Land monthly); trial year 2020 for AgERA5 daily |
| Spatial coverage | All-India bounding box |
| Spatial unit or resolution | 0.1° (ERA5-Land, AgERA5); 0.5° (agroclimatic indicators) |
| Temporal resolution | Monthly / daily |
| Licence | Licence to use Copernicus Products (free, worldwide, for any purpose including commercial, with attribution). Accept it on each dataset's download page; record the version accepted here |
| OK for a public open-source app? | OK with attribution (confirm on acceptance) |
| Required attribution text | "Contains modified Copernicus Climate Change Service information [year]" (plus dataset DOI) |
| Citation | Muñoz Sabater, J. (2019). ERA5-Land monthly averaged data from 1950 to present. C3S CDS. DOI 10.24381/cds.68d2bb30 ; Boogaard, H. et al. (2020). Agrometeorological indicators from 1979 to present derived from reanalysis. C3S CDS. DOI 10.24381/cds.6c68c9bb |
| Files in this folder | None yet. The script writes to `08_solar_weather/tmy/raw/cds/` and `01_agro_climate/temperature/raw/agera5/` (git-ignored) |
| Units and key column meanings | ERA5-Land: `t2m` K; `tp` m/day (monthly means of daily totals); `ssrd` J m⁻² accumulated per day, so divide by 3.6e6 for kWh m⁻² day⁻¹ |
| Known caveats and gaps | (1) **Blocked on you:** Claude cannot create accounts, enter API keys or accept licence terms. Sign in, accept the licences, and put your key in `~/.cdsapirc`; then run the script yourself or ask Claude to. (2) The CDS has announced "service protection measures" (6 Oct 2026) that may queue or throttle large requests, so keep requests to one variable-year batch. (3) ERA5-Land `ssrd` is a reanalysis estimate: use it for spatial patterns and seasonality, and calibrate against NREL NSRDB / Global Solar Atlas / PVGIS for D14 energy figures |
| Processing notes | None yet. Planned: area-weighted district means of each variable against D00 polygons (exactextract) |
