# Source candidates: found, not yet downloaded

Sources identified on 2026-11-06 that fill open gaps in `DATA_REQUIREMENTS.md` but were not downloaded in this
pass. Each needs either your account or a licence check, or is large. When you take one, create its
`SOURCE_*.md` card in the target folder and remove the row here.

| Gap | Candidate | Why it fits | Blocker / next step | Target folder |
|---|---|---|---|---|
| D02 / D03 district rainfall and temperature, daily 1901–present | **IMD gridded data**: rainfall 0.25°, Tmax/Tmin 1° (imdpune.gov.in → Gridded Data) | Official national standard; better than reanalysis for rainfall | Free download (binary `.grd` per year); needs a small reader (e.g. `imdlib`) and ~1 GB for 1991–2020 | `01_agro_climate/rainfall/`, `temperature/` |
| D02 / D03 / D14 high-resolution agro-met | **AgERA5 / ERA5-Land** (Copernicus CDS) | 0.1° daily, built for crop models | **Needs your CDS account + licence acceptance**; script ready: `_scripts/fetch_cds_india.py` | `08_solar_weather/tmy/` |
| D06 cropland mask by season | **NRSC Bhuvan LULC 250K** annual raster (Kharif / Rabi / Zaid / double-crop classes) | Exactly the seasonal cropland split the model needs | Needs a free Bhuvan login (only you can create it); technical document already in `04_land_cover/` | `04_land_cover/raw/` |
| D06 alternative (open) | **ESA WorldCover 2021** 10 m (CC BY 4.0) | Open licence; cropland class | ~35 tiles (≈ 2–4 GB) for India; no seasonal split | `04_land_cover/raw/` |
| D05 elevation and slope | **Copernicus DEM GLO-90** (AWS open data, free licence) | Open global DEM, good for district mean elevation and slope | ~300 tiles × 1° for India (≈ 3 GB); pick 90 m to stay small | `03_elevation/raw/` |
| D01 60 agro-ecological sub-regions | NBSS&LUP AESR map (Bhuvan / ICAR publication 2015 revision) | The FAO and India-WRIS layers only have the 20 regions | Find a downloadable layer; check ICAR terms | `01_agro_climate/zones/` |
| D11 crop calendars | **SAGE crop calendar** (Sacks et al. 2010), gridded planting/harvest for 19 crops | Open, global, includes Indian regions | Authors ask downloaders to email Bill Sacks (courtesy). Also check MIRCA2000 and DES Farm Harvest Prices "harvest season" tables | `06_crops/crop_calendar/` |
| D11 Indian crop-weather calendars | IMD Agromet district crop-weather calendars | District-specific sowing / harvest windows by standard week | Scattered PDFs per state; extraction work | `06_crops/crop_calendar/` |
| D13 realised prices | **Agmarknet daily mandi prices** (data.gov.in API, GODL) | Modal prices incl. onion, potato, tomato | data.gov.in API key needs **your** account; alternative: DES Farm Harvest Prices 2022-23 PDF (desagri.gov.in) | `07_crop_economics/prices/` |
| D10 horticulture by district | NHB / DA&FW Horticulture Statistics (district-wise area and production) | Fills the remaining vegetable gap (UPAg lacks horticulture) | Locate the latest district-wise release (desagri / NHB); PDFs or XLS | `06_crops/area_production_yield/` |
| D09 landholdings | Agriculture Census 2015-16 / 2021-22 (agcensus.da.gov.in) district tables | Number and area of holdings by size class | Report-builder site; may need per-state export | `05_groundwater_irrigation/landholdings/` |
| D08 irrigation and pumps | 7th Minor Irrigation Census (2023 report, Ministry of Jal Shakti) | Wells, tube wells, pump energy source by district | Large PDF / data.gov.in tables | `05_groundwater_irrigation/irrigation_and_pumps/` |
| D07 cross-check | Dataful district-wise stage of extraction 2004–2025 | Time series of CGWB categories | Third-party compilation; licence to check | `05_groundwater_irrigation/cgwb_assessment/` |
| D19 state tariffs | State SERC orders for PM-KUSUM Component A levelised tariff (e.g. Rajasthan, Maharashtra, MP, Gujarat) | Needed for district default tariffs | Collect order PDFs per state; record ₹/kWh and order date | `11_finance_policy/kusum/` |
| D20 CAPEX / O&M | MNRE benchmark costs; CERC RE tariff regulations; recent tenders (SECI, state agencies) | ₹/kWp benchmarks for ground-mount and elevated structures | Collect and tabulate | `11_finance_policy/capex_om/` |
