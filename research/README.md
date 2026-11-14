# research/

All raw data, literature and research notes for AgriPV Lab live here. **Start with
[`DATA_REQUIREMENTS.md`](DATA_REQUIREMENTS.md)**: it lists every dataset (D00 to D25), why it is needed, the exact
fields to collect, and when it counts as done.

| Folder | Datasets |
|---|---|
| `00_admin_boundaries/` | D00: district list, LGD codes, boundaries, mapping |
| `01_agro_climate/` (`zones/`, `rainfall/`, `temperature/`) | D01 to D03 |
| `02_soil/` | D04 |
| `03_elevation/` | D05 |
| `04_land_cover/` | D06: cropland mask |
| `05_groundwater_irrigation/` (`cgwb_assessment/`, `irrigation_and_pumps/`, `landholdings/`) | D07 to D09 |
| `06_crops/` (`area_production_yield/`, `crop_calendar/`) | D10, D11 |
| `07_crop_economics/` (`cost_of_cultivation/`, `prices/`) | D12, D13 |
| `08_solar_weather/` (`tmy/`, `solar_atlas/`, `albedo/`) | D14, D15 |
| `09_crop_shade_response/` (`papers/`, `extraction/`, `parameters/`) | D16: the riskiest research |
| `10_validation/` (`field_trials/`, `energy_reference/`) | D17, D18 |
| `11_finance_policy/` (`kusum/`, `capex_om/`, `lending_tax/`, `land_lease/`, `yield_limit_policy/`) | D19 to D23 |
| `12_structures_technology/` | D24 |
| `13_stakeholder_notes/` | D25 |
| `_templates/` | `SOURCE.md` provenance card |
| `_scripts/` | Small, re-runnable fetch / extract scripts referenced from SOURCE cards |
## Rules
1. Every source gets a `SOURCE.md` (copy from `_templates/`) **before** you process it. When a folder holds
   more than one source, name the cards `SOURCE_<publisher>_<dataset>.md`.
2. Large downloads go in the folder's `raw/`, which is git-ignored. Small CSVs and notes are committed.
3. Join on **LGD codes**, never on district names.
4. Paper PDFs stay local (git-ignored). Commit citations and extracted numbers only.
5. No personal data anywhere in the repo.
6. Commit data files (outside `raw/`) only when the card's "OK for a public open-source app?" field says OK.
   Restricted or unknown licences stay in `raw/`.
7. The MIT licence covers the code only. Each committed data table keeps its source's licence (CC BY 4.0, GODL-India,
   ODC-By, ODbL, Copernicus). The app's data-sources page must carry every card's attribution text, including the
   Copernicus DEM liability disclaimer.
8. District rainfall, soil and terrain tables come in two versions, area- and cropland-weighted. The model uses the
   `*_cropland.csv` files; the area versions are kept for comparison.

## Source register

| Card | Dataset | Status | Licence | In git |
|---|---|---|---|---|
| [`00_admin_boundaries/SOURCE_datta07_indian_shapefiles.md`](00_admin_boundaries/SOURCE_datta07_indian_shapefiles.md) | D00 | Downloaded | MIT | Attribute CSVs (no geometry) |
| [`01_agro_climate/zones/SOURCE_fao_gaez_aer_india.md`](01_agro_climate/zones/SOURCE_fao_gaez_aer_india.md) | D01 | Downloaded (20 AERs, not 60 AESRs); superseded | No licence (restricted) | No |
| [`01_agro_climate/rainfall/SOURCE_worldbank_cckp_era5.md`](01_agro_climate/rainfall/SOURCE_worldbank_cckp_era5.md) | D02 | Downloaded (state level) | Likely CC BY 4.0, to confirm | State climatology CSV |
| [`01_agro_climate/temperature/SOURCE_worldbank_cckp_era5.md`](01_agro_climate/temperature/SOURCE_worldbank_cckp_era5.md) | D03 | Downloaded (state level) | Likely CC BY 4.0, to confirm | State climatology CSV |
| [`01_agro_climate/rainfall/SOURCE_chirps_v3.md`](01_agro_climate/rainfall/SOURCE_chirps_v3.md) | D02 | Downloaded; district normals and CV 1991–2020 (primary rainfall source) | Public domain / CC BY 4.0 | `chirps_v3_district_rainfall_normals_1991-2020.csv` |
| [`01_agro_climate/rainfall/SOURCE_imd_rainfall.md`](01_agro_climate/rainfall/SOURCE_imd_rainfall.md) | D02 | District normals 1971–2020 saved locally for QA only | Restricted (IMD) | No |
| [`01_agro_climate/CLIMATE_INDICATOR_METHODS.md`](01_agro_climate/CLIMATE_INDICATOR_METHODS.md) | D02/D03 | Method spec: sources, cropland weighting, indicator definitions | n/a | Yes |
| [`01_agro_climate/SOURCE_niti_iced_climate.md`](01_agro_climate/SOURCE_niti_iced_climate.md) | D02/D03 | Reviewed, not used | Unstated | No |
| [`02_soil/SOURCE_kaggle_lockhal_soil_environment.md`](02_soil/SOURCE_kaggle_lockhal_soil_environment.md) | D04 | Downloaded | CC BY 4.0 (compiler); ICAR upstream unclear | No |
| [`02_soil/SOURCE_isric_soilgrids_v2.md`](02_soil/SOURCE_isric_soilgrids_v2.md) | D04 | Downloaded; district 0–30 cm topsoil (clay, silt, sand, pH, SOC, bulk density, CEC) | CC BY 4.0 | `soilgrids_v2_district_topsoil_0-30cm.csv` |
| [`03_elevation/SOURCE_copernicus_dem_glo90.md`](03_elevation/SOURCE_copernicus_dem_glo90.md) | D05 | Downloaded; district elevation and slope-class shares | Copernicus DEM (free, attribution + disclaimer) | `copdem_glo90_district_terrain.csv` |
| [`04_land_cover/SOURCE_esa_worldcover_2021.md`](04_land_cover/SOURCE_esa_worldcover_2021.md) | D06 | Downloaded; 0.01° cropland fraction, district cropland and cropland centroids; weights the rainfall, soil and terrain tables | CC BY 4.0 | `worldcover_2021_district_cropland.csv` |
| [`06_crops/SOURCE_kaggle_aartithube_district_crops_soil_health.md`](06_crops/SOURCE_kaggle_aartithube_district_crops_soil_health.md) | D10/D04 | Downloaded | Non-commercial only | No |
| [`06_crops/area_production_yield/SOURCE_upag_des_district_apy.md`](06_crops/area_production_yield/SOURCE_upag_des_district_apy.md) | D10 | Downloaded 2013-14 to 2024-25; national crop ranking (Q-04) built | Permission needed (UPAg copyright policy) | `top20_national.csv` (national totals only) |
| [`08_solar_weather/SOURCE_copernicus_cds.md`](08_solar_weather/SOURCE_copernicus_cds.md) | D14/D02/D03/D15 | **Needs your CDS account** | Copernicus licence (open) | No |
| [`11_finance_policy/lending_tax/SOURCE_global_macro_database.md`](11_finance_policy/lending_tax/SOURCE_global_macro_database.md) | D21 | Downloaded (India extract) | Research-only, no products | No |
| [`00_admin_boundaries/SOURCE_lgd_directory.md`](00_admin_boundaries/SOURCE_lgd_directory.md) | D00 | Downloaded (snapshot 2026-11-01) | Govt public directory (GODL) | `lgd_states.csv`, `lgd_districts.csv` |
| [`01_agro_climate/zones/SOURCE_indiawris_aer_shapefile.md`](01_agro_climate/zones/SOURCE_indiawris_aer_shapefile.md) | D01 | Uploaded by owner (20 AERs with codes) | GODL-India (via data.gov.in) | Shapefile (uploaded) |
| [`01_agro_climate/zones/SOURCE_bharatlas_agro_zones.md`](01_agro_climate/zones/SOURCE_bharatlas_agro_zones.md) | D01 | Downloaded; district × zone crosswalk built (15 ACZ, 20 AER) | GODL-India | `district_zone_shares.csv`, `district_zone_primary.csv` |
| [`00_admin_boundaries/SOURCE_bharatlas_lgd_districts.md`](00_admin_boundaries/SOURCE_bharatlas_lgd_districts.md) | D00 | Downloaded (785 LGD-coded polygons) | CC BY 4.0 / CC0 | No (geometry in `raw/`) |
| [`04_land_cover/SOURCE_nrsc_lclu_250k.md`](04_land_cover/SOURCE_nrsc_lclu_250k.md) | D06 | Uploaded by owner (document + map image; raster still needed) | Unrestricted document; Bhuvan terms for data | PDFs (uploaded) |
| [`05_groundwater_irrigation/cgwb_assessment/SOURCE_cgwb_dgwr.md`](05_groundwater_irrigation/cgwb_assessment/SOURCE_cgwb_dgwr.md) | D07 | 2025 and 2024 editions extracted (709 / 715 districts) plus 2025 unit categories; reconciled to national totals | Public Govt report | `cgwb_dgwr_2025_district.csv`, `cgwb_dgwr_2025_district_unit_categories.csv`, `cgwb_dgwr_2024_district.csv` |
| [`05_groundwater_irrigation/cgwb_assessment/SOURCE_nwic_groundwater_levels.md`](05_groundwater_irrigation/cgwb_assessment/SOURCE_nwic_groundwater_levels.md) | D07 | Downloaded; district pre/post-monsoon depth 2021–2025 (552 districts) | NWIC: free reproduction with attribution | `nwic_gwl_district_depth_2021-2025.csv` |
| [`06_crops/area_production_yield/SOURCE_dafw_horticulture_estimates.md`](06_crops/area_production_yield/SOURCE_dafw_horticulture_estimates.md) | D10 | Downloaded (Final 2023-24 and 2024-25, state × crop); national areas merged into the crop ranking | Permission needed (DA&FW website policy) | National totals in `top20_national.csv` only |
| [`06_crops/crop_calendar/SOURCE_ggcmi_phase3_crop_calendar.md`](06_crops/crop_calendar/SOURCE_ggcmi_phase3_crop_calendar.md) | D11 | Downloaded; district planting / maturity dates for 18 crops (irrigated and rainfed), QA-flagged | CC BY 4.0 | `ggcmi_phase3_district_crop_calendar.csv` |
| [`06_crops/area_production_yield/SOURCE_des_horizontal_crop_report.md`](06_crops/area_production_yield/SOURCE_des_horizontal_crop_report.md) | D10 | Uploaded by owner (incl. horticulture, 26 states) | Govt data, licence to confirm | Report (uploaded) |
| [`09_crop_shade_response/papers/SOURCE_laub_2022_shade_metaanalysis.md`](09_crop_shade_response/papers/SOURCE_laub_2022_shade_metaanalysis.md) | D16 | In progress: 252 treatment rows from 19 sources (Indian trials on a season-mean light basis), draft `(L_t, k)` and grades for the 20 crops (8 of the top 10 at grade B or better; only cumin at D); status in [`09_crop_shade_response/EVIDENCE_STATUS.md`](09_crop_shade_response/EVIDENCE_STATUS.md) | CC BY 4.0 (meta-analysis); papers cited, PDFs local | `shade_response_extraction.csv`, `bibliography.csv`, `crop_parameters_draft.csv`, `group_curves_laub2022.csv` |
| [`07_crop_economics/cost_of_cultivation/SOURCE_idp_des_cost_of_cultivation.md`](07_crop_economics/cost_of_cultivation/SOURCE_idp_des_cost_of_cultivation.md) | D12 | Downloaded (state × crop, 1996–2022) | ODC-By | Yes |
| [`07_crop_economics/prices/SOURCE_pib_msp.md`](07_crop_economics/prices/SOURCE_pib_msp.md) | D13 | Transcribed (KMS 2026-27, RMS 2027-28) | Govt press release | Yes |
| [`07_crop_economics/prices/SOURCE_des_farm_harvest_prices.md`](07_crop_economics/prices/SOURCE_des_farm_harvest_prices.md) | D13 | Downloaded (2022-23); state summary extracted | Govt publication, likely OK | `fhp_state_major_crops_2019-2023.csv` |
| [`08_solar_weather/solar_atlas/SOURCE_global_solar_atlas.md`](08_solar_weather/solar_atlas/SOURCE_global_solar_atlas.md) | D14/D18 | Downloaded, sampled per district | CC BY 4.0 | `gsa_district_centroid_stats.csv` |
| [`08_solar_weather/solar_atlas/SOURCE_nasa_power.md`](08_solar_weather/solar_atlas/SOURCE_nasa_power.md) | D02/D03/D14 | Downloaded per district (2001–2020 climatology) | Public, no restrictions | `nasa_power_district_climatology_2001-2020.csv` |
| [`11_finance_policy/kusum/SOURCE_mnre_pm_kusum.md`](11_finance_policy/kusum/SOURCE_mnre_pm_kusum.md) | D19 | Downloaded (11 MNRE documents) | Govt documents | `kusum_component_a_rules.md` |

Sources found but not yet downloaded (account needed, large, or licence unclear) are listed in
[`SOURCE_CANDIDATES.md`](SOURCE_CANDIDATES.md).
