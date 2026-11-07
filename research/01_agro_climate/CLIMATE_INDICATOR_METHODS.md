# Climate indicators: definitions and aggregation method (D02, D03)

How AgriPV Lab turns gridded daily or monthly climate data into one row per LGD district. Baseline period:
**1991–2020** (WMO standard normal; 10,958 days, 8 leap years).

## Sources (decided)

| Variable | Primary | Cross-checks | Why |
|---|---|---|---|
| Rainfall | **CHIRPS v3.0** (0.05°, monthly / daily, 1981–present; public domain / CC BY 4.0), **used as-is with no bias scaling** | IMD district normals 1971–2020 (local only, licence restricted); NASA POWER; CCKP ERA5 (state) | Open licence plus the finest grid (≈ 5.5 km); IMD 0.25° gridded rainfall has no open licence on its download pages. CHIRPS runs about 13% wetter than IMD gauge normals (median of 552 districts); disclose this on the methodology page |
| Temperature (Tmax / Tmin / Tmean) | **ERA5-Land** daily statistics (0.1°, 1950–present; Copernicus licence) via CDS, **blocked on your CDS account** | NASA POWER (0.5°, MERRA-2); CCKP ERA5 (state) | ERA5-Land applies a lapse-rate correction at 9 km. IMD gridded temperature is 1° and its station count drops to about 180 from 2008 |
| Solar | Global Solar Atlas (PVOUT, GHI) | NASA POWER | Already in `08_solar_weather/solar_atlas/` |

## Spatial aggregation

1. **Cell weights.** For each district *d* and grid cell *i*: `w_id = f_id × cos(lat_i) × c_i`, where `f_id` is the
   fraction of the cell inside the district polygon (LGD-coded polygons, rasterised at 1/5 of the cell size),
   `cos(lat)` corrects cell area, and `c_i` is the cell's **cropland fraction**.
2. **Cropland fraction** `c_i`: ESA WorldCover 10 m (v200 2021, CC BY 4.0), class 40 (Cropland), averaged onto the
   climate grid. **Done (2026-11-07):** the 0.01° cropland fraction is in
   `04_land_cover/raw/worldcover_2021/`; tables come in two versions, `weighting = "area"` and
   `weighting = "cropland"` (`*_cropland.csv`, the default for the model). If a district has no cropland cell with
   data, it falls back to area weights and sets `cropland_fallback = true`.
3. **Order of operations.** Linear indicators (seasonal totals and means, GDD, PET) can be averaged in any order.
   **Non-linear indicators (CV, threshold-day counts, rainy days) are computed per cell first, then weighted.**
   Averaging rain across a district before applying a 2.5 mm threshold inflates rainy days and suppresses variance.

## Indicator definitions

| Indicator | Definition | Notes |
|---|---|---|
| Seasonal rainfall normals | Mean over 30 years of totals for JF, MAM, **JJAS** (SW monsoon) and **OND** (post-monsoon), plus monthly and annual | IMD seasons |
| CV of rainfall (%) | `100 × sd / mean` over the 30 annual (or JJAS / OND) totals, sample sd (ddof = 1), per cell then weighted | Flag seasons with mean < 10 mm, where CV becomes meaningless (> 150%) |
| Rainy days | Days with rainfall **≥ 2.5 mm** (IMD definition), mean count per year / per season | Needs daily data (CHIRPS daily); not the 1 mm CCKP wet-day threshold |
| Hot days | Days per year with **Tmax > 40 °C** (IMD heatwave baseline for plains) | Needs daily Tmax (ERA5-Land) |
| Terminal heat (rabi) | Days in **Feb–Mar with Tmax > 35 °C** (59 or 60 days) | Wheat grain-filling stress, so shading is a potential benefit |
| GDD | `max(0, (Tmax + Tmin)/2 − Tbase)` summed per season; Tbase **10 °C** for kharif crops (rice, maize, soybean, pigeonpea) and **5 °C** for rabi wheat / barley | Report the base used; optional upper cap of 30–35 °C |
| PET (Hargreaves–Samani) | `ET0 = 0.0023 × (Tmean + 17.8) × (Tmax − Tmin)^0.5 × 0.408 × Ra` (FAO-56 eq. 52; Ra from latitude and day of year, eqs. 21–25) | Use monthly or longer sums |
| Aridity index | `AI = P / PET` (30-year annual means). UNEP classes: hyper-arid < 0.05; arid 0.05–0.20; semi-arid 0.20–0.50; dry sub-humid 0.50–0.65; humid > 0.65 | Core context for the water-saving case for AgriPV |

## Primary references

- IMD, *Glossary* (rainy day ≥ 2.5 mm; heatwave criteria): https://www.imdpune.gov.in/Reports/glossary.pdf
- Allen, R. G. et al. (1998). *FAO Irrigation and Drainage Paper 56*, eqs. 21–25 and 52.
- Middleton, N. & Thomas, D. (1997). *World Atlas of Desertification*, 2nd ed., UNEP (aridity classes).
- Funk, C. et al. (2026). The Climate Hazards Center Infrared Precipitation with Stations, Version 3. *Scientific Data* 13, 718.
- Muñoz-Sabater, J. et al. (2021). ERA5-Land. *Earth Syst. Sci. Data* 13, 4349–4383.
