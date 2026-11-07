# AgriPV Lab — Research & Data Requirements

This is the research backbone of the project. It lists **every dataset and research input** that AgriPV Lab needs, why each one is needed, the exact fields to collect, and when it counts as done. Each item has an ID (`D00`–`D25`) and a matching folder under `research/`.

- **Spec this serves:** [`docs/superpowers/specs/2026-11-06-agripv-lab-product-spec.md`](../docs/superpowers/specs/2026-11-06-agripv-lab-product-spec.md) (§7.3 quality targets, §12 model, §13 crop evidence, §14 data).
- **Unit of analysis:** the **district** (~780, keyed by LGD code). Raster data is averaged over **cropland only**.
- **The sources named are candidates.** Confirm each one's access, current version and **licence** before relying on it. Record the outcome in that folder's `SOURCE.md` (template in `_templates/`).

---

## Quick reference

| ID | Dataset | Feeds | Priority | Folder |
|---|---|---|---|---|
| D00 | District list, LGD codes, boundaries, old-to-new district mapping | Everything | **Critical** | `00_admin_boundaries` |
| D01 | Agro-climatic and agro-ecological zones | Context, insights | High | `01_agro_climate/zones` |
| D02 | Rainfall (gridded, daily) | Context, seasons, insights | High | `01_agro_climate/rainfall` |
| D03 | Temperature and heat-stress days | Context, heat insight, heat uplift (P1) | High | `01_agro_climate/temperature` |
| D04 | Soil properties | Context | Medium | `02_soil` |
| D05 | Elevation and slope | Context, flat-cropland filter | Medium | `03_elevation` |
| D06 | Land cover / cropland mask | Weighting for every raster | **Critical** | `04_land_cover` |
| D07 | Groundwater status (CGWB) | Context, insights, screening | High | `05_groundwater_irrigation/cgwb_assessment` |
| D08 | Irrigation, wells and pump energy source | Context, KUSUM relevance | Medium | `05_groundwater_irrigation/irrigation_and_pumps` |
| D09 | Operational landholdings | Context, plant-size realism | Medium | `05_groundwater_irrigation/landholdings` |
| D10 | Crop area, production, yield (district, season) | Default rotation, baseline yield | **Critical** | `06_crops/area_production_yield` |
| D11 | Crop calendars (sowing/harvest months) | Season light averaging | **Critical** | `06_crops/crop_calendar` |
| D12 | Cost of cultivation | Farm income | **Critical** | `07_crop_economics/cost_of_cultivation` |
| D13 | Crop prices (MSP, mandi, farm harvest) | Farm income | **Critical** | `07_crop_economics/prices` |
| D14 | Solar resource + hourly typical year (TMY) | Physics simulation | **Critical** | `08_solar_weather` |
| D15 | Ground albedo | Bifacial gain (physics) | Low | `08_solar_weather/albedo` |
| D16 | Crop shade-response literature | Crop parameters (L_t, k), evidence grades | **Critical — riskiest** | `09_crop_shade_response` |
| D17 | Field-trial observations for validation | Yield validation (±15 pp target) | **Critical** | `10_validation/field_trials` |
| D18 | Energy reference values | Energy validation (±3% / ±7%) | High | `10_validation/energy_reference` |
| D19 | PM-KUSUM rules and state tariffs | Finance defaults | **Critical** | `11_finance_policy/kusum` |
| D20 | CAPEX and O&M benchmarks | Finance defaults | **Critical** | `11_finance_policy/capex_om` |
| D21 | Lending, tax and depreciation terms | Finance defaults, Advanced (P1) | High | `11_finance_policy/lending_tax` |
| D22 | Land lease benchmarks | Lease model defaults, sanity checks | High | `11_finance_policy/land_lease` |
| D23 | Yield-limit policy and international APV standards | Policy line, Method page | High | `11_finance_policy/yield_limit_policy` |
| D24 | Structure and module technology parameters | Structure presets, a_farm, efficiency | High | `12_structures_technology` |
| D25 | Stakeholder interviews and policymaker notes | Q-01–Q-03, validation, success metrics | High | `13_stakeholder_notes` |

---

## A. Geography and administration

### D00 — District list, LGD codes and boundaries (Critical)
**Why:** Every other dataset is joined on the district. Errors here spread into every number downstream.

**Collect:**
1. The **LGD district list**: state name and LGD state code, district name and LGD district code, and alternative or older spellings.
2. **District change history**: districts created, split or renamed, with the date and parent district(s). This is needed to map older data (ICRISAT, older DES years) onto today's districts.
3. **District boundary polygons** for recent boundaries, matching the LGD list. Plus a **national outline that complies with Survey of India's depiction of India's boundaries**: a public Indian map must show the official boundaries.
4. An **alias table**: common transliteration variants and renamed districts (e.g. Gurgaon → Gurugram). The district search uses it (REQ-DIS-01).

**Candidate sources:**
- Local Government Directory (LGD, MoPR) for codes and change history.
- Survey of India / Bhuvan for official boundaries.
- Community boundary sets (DataMeet, geoBoundaries) as working geometry. **Check their licences.**
- GADM is non-commercial only; avoid it if possible.

**Format:** CSV for lists and mappings; GeoPackage or Shapefile (EPSG:4326) for polygons.

**Done when:**
- Every district has an LGD code and a polygon.
- The polygons cover India with no gaps or overlaps.
- The old-to-new mapping covers every district created since 1966 (the ICRISAT baseline).

---

## B. Agro-climate

### D01 — Agro-climatic and agro-ecological zones (High)
**Why:** District context panel, insights, screening filters (REQ-CTX-01, REQ-SCR-01).

**Collect:**
- Planning Commission **15 agro-climatic regions** (with sub-zones): district → zone mapping.
- NBSS&LUP **agro-ecological regions (20) and sub-regions (~60)**: polygons or a district mapping.
- Optional: the ICAR-NARP **agro-climatic zones (~127)**, which are finer and widely used by state agricultural universities.

**Candidate sources:**
- Planning Commission documents.
- NBSS&LUP publications and maps.
- ICAR-CRIDA **District Agriculture Contingency Plans**. These list the zone, soils, rainfall and crop calendar per district and are a very useful cross-check.

**Done when:** every district has a zone and a sub-region, with the source year recorded.

### D02 — Rainfall (High)
**Why:** kharif, rabi and annual rainfall normals; the aridity index; insights.

**Collect:**
- **Daily gridded rainfall**, ideally 30+ years (e.g. 1991–2020).
- Derived per district: annual normal, Jun–Sep (monsoon) and Oct–Dec normals, rainfall in kharif/rabi/zaid months, coefficient of variation (rainfall variability), and the number of rainy days.

**Candidate sources:**
- IMD Pune gridded rainfall (0.25°, daily).
- Alternatives: CHIRPS (0.05°), ERA5-Land.

**Licence check:** IMD's terms for redistributing derived data in a public app (open question Q-05).

**Done when:** every district has normals computed over cropland, and the period and method are recorded.

### D03 — Temperature and heat stress (High)
**Why:** the heat-stress insight; the optional heat-relief uplift (REQ-CRP-05); context.

**Collect:**
- Daily Tmax and Tmin (gridded).
- Derived per district: mean Tmax/Tmin per season, **average days per year with Tmax > 40 °C**, days > 35 °C in the rabi grain-filling months (Feb–Mar), and growing degree days per season.
- Inputs for the aridity index: PET, or Tmax/Tmin plus radiation for a Hargreaves estimate.

**Candidate sources:**
- IMD gridded temperature (1°, daily).
- ERA5-Land (0.1°) or NASA POWER for finer resolution.

**Done when:** every district has heat-day counts and seasonal means, with the method recorded.

---

## C. Land

### D04 — Soil (Medium)
**Why:** the context panel. Soil also explains why yields vary between districts.

**Collect, cropland-weighted per district:**
- Texture class (from clay/silt/sand %).
- Topsoil pH, organic carbon, bulk density, CEC.
- Depth to bedrock or effective soil depth.
- Dominant soil order (e.g. Vertisols, Alfisols).

**Candidate sources:**
- ISRIC SoilGrids 250 m (v2.0, CC BY 4.0).
- NBSS&LUP 1:250k soil maps for soil orders.
- Soil Health Card data is optional (it's hard to obtain in bulk).

**Done when:** every district has a texture class, pH, organic carbon and soil depth, with the SoilGrids version recorded.

### D05 — Elevation and slope (Medium)
**Why:** context; the "flat cropland" filter; structure feasibility.

**Collect, cropland-weighted:**
- Mean, P10 and P90 elevation.
- Mean slope.
- **% of cropland with slope < 5°** (also < 2° and < 8° for sensitivity).

**Candidate sources:**
- Copernicus GLO-30 DEM (free; attribution required).
- SRTM 30 m.
- CartoDEM (Bhuvan).

**Done when:** every district has slope statistics, with the DEM and slope method recorded.

### D06 — Land cover and cropland mask (Critical)
**Why:** every raster statistic is averaged over **cropland only**. Without this mask, forest and hill land distort soil, slope and solar values.

**Collect:**
- A cropland mask at 10–30 m.
- Per district: cropland area (ha) and cropland share of district area.
- The **cropland centroid** (where the solar TMY is taken).

**Candidate sources:**
- ESA WorldCover 10 m (2020/2021, CC BY 4.0).
- Alternatives: Dynamic World, Bhuvan LULC.

**Done when:**
- The mask covers India.
- District cropland areas agree with DES net sown area within a reasonable tolerance. Record the difference for each district.

---

## D. Water and farm structure

### D07 — Groundwater status (High)
**Why:** groundwater-stress context, insights and screening. Solar pumping in over-exploited blocks is a real policy risk.

**Collect, per assessment unit (block, mandal or taluka) for the latest year:**
- **Category**: safe, semi-critical, critical, over-exploited or saline.
- **Stage of groundwater extraction (%)**.
- Annual extractable resource and current draft.
- Aggregated per district: **share of units in each category** (by count and by area) and mean stage of extraction.
- Optional: pre- and post-monsoon water-table depth trends.

**Candidate sources:**
- CGWB *Dynamic Ground Water Resources of India* (latest assessment year), and the INGRES portal.
- India-WRIS for well levels.

**Done when:**
- Every district has its category shares and stage of extraction, with the assessment year recorded.
- Units are mapped to LGD districts.

### D08 — Irrigation, wells and pump energy source (Medium)
**Why:** irrigation context. The share of electric, diesel and solar pumps shows how relevant PM-KUSUM is.

**Collect per district:**
- Net and gross irrigated area, and irrigation by source (canal, tank, tube-well, other wells, other).
- From the Minor Irrigation Census: number of dug wells, shallow and deep tube-wells, and the **pump energy source** (electric, diesel, solar, manual).

**Candidate sources:**
- DES Land Use Statistics.
- Minor Irrigation Census (latest round).
- ICRISAT district database for historical series.

**Done when:** every district has its irrigation share and pump energy mix, with the census year recorded.

### D09 — Operational landholdings (Medium)
**Why:** smallholder context. It also tests whether 0.5–2 MW KUSUM-A plants (about 2–8 acres each) are realistic without pooling land through FPOs.

**Collect per district:** number and area of holdings by size class (marginal < 1 ha, small 1–2 ha, semi-medium, medium, large), and the average holding size.

**Candidate source:** Agriculture Census (latest round).

**Done when:** every district has its size-class distribution and average holding size.

---

## E. Crops and crop economics

### D10 — Crop area, production and yield (Critical)
**Why:** the default crop rotation (the main crop by area in each season) and the **baseline yield** in the farm-income model (REQ-MOD-03).

**Collect per district × crop × season × year, for the latest 5–10 years:**
- Area (ha), production (t, or bales for cotton) and yield (kg/ha).
- Season: kharif, rabi, zaid/summer, or whole year.

Then derive a **5-year average** and the **top crops by area per season**.

**Candidate sources:**
- DES Crop Production Statistics (district-wise APY).
- ICRISAT District Level Database for gaps and long series. It uses 1966 boundaries, so map it through D00.

**Done when:**
- ≥ 90% of districts have the main crops for each season with yields.
- Gaps are flagged.
- The unit conversions (bales, nuts, etc.) are documented.

### D11 — Crop calendars (Critical)
**Why:** shade is averaged over **the months the crop is actually in the field**. The spec's default season windows (kharif Jun–Oct, rabi Nov–Mar, zaid Mar–Jun) should be refined per crop and region.

**Collect per crop × state (or agro-climatic zone):**
- Sowing month window, harvest month window and duration (days).
- Critical growth stages (e.g. flowering, grain filling), since those are when shade matters most.

**Candidate sources:**
- ICAR-CRIDA district contingency plans.
- State agricultural university package-of-practices.
- FAO crop calendars.
- IMD agromet advisories.

**Done when:** each of the top 20 crops has a calendar for every zone where it's grown.

### D12 — Cost of cultivation (Critical)
**Why:** farm income = yield × price − cost (spec §12.4).

**Collect per crop × state × year (latest 3–5 years):**
- Cost per hectare. Record which **cost concept** each figure is (A2, A2+FL, C2), and keep it consistent. **Recommended: A2+FL**, which matches how MSP is set.
- Yield per hectare as reported in the survey.
- Main cost items, if available: labour, seed, fertiliser, irrigation, machinery.

**Candidate sources:**
- CACP *Price Policy* reports (kharif and rabi).
- DES Cost of Cultivation Scheme.
- State agriculture departments.

**Done when:**
- The top 20 crops have state-level costs for their main producing states.
- The cost concept and year are recorded, and costs are inflated to a common base year (with the method recorded).

### D13 — Crop prices (Critical)
**Why:** farm income.

**Collect per crop:**
- **MSP** by year (for MSP crops).
- **Mandi modal prices**: monthly median by district or state, and the harvest-month average.
- **Farm harvest prices** where available.
- Decide which price the model uses. **Recommended: the harvest-season median of mandi modal prices, with MSP as a floor for MSP crops**, recorded per crop.

**Candidate sources:**
- CACP / MoA&FW MSP notifications.
- Agmarknet (check its terms, Q-05).
- DES Farm Harvest Prices.

**Done when:** every top-20 crop has a price for each state, with the method and year recorded.

---

## F. Solar resource and weather for physics

### D14 — Solar resource and typical-year weather (Critical)
**Why:** drives the pvlib energy and ground-light simulation for every district (spec §12.1).

**Collect per district, at the cropland centroid from D06:**
- An **hourly TMY (typical meteorological year)** with GHI, DNI, DHI, air temperature, wind speed and relative humidity.
- Annual and monthly GHI, DNI and DHI.
- PV output (kWh/kWp) as a cross-check.
- The diffuse fraction by month. Monsoon diffuse light matters for the crop result.

**Candidate sources:**
- PVGIS (EU JRC; the ERA5-based TMY has global coverage).
- Global Solar Atlas (World Bank/Solargis, CC BY 4.0) for GHI/DNI/PVOUT maps.
- NASA POWER (hourly).
- NREL NSRDB South Asia.
- NIWE ground stations for spot validation.

**Done when:**
- Every district has an hourly TMY.
- Annual GHI from the TMY is within ±5% of Global Solar Atlas, and any district outside that is flagged.

### D15 — Ground albedo (Low)
**Why:** bifacial modules gain energy from light reflected off the ground, and the reflectance changes with crop cover and season.

**Collect:** monthly surface albedo per district over cropland.

**Candidate source:** MODIS albedo product, or the albedo embedded in the TMY.

**Done when:** every district has monthly albedo, or a documented default of 0.2.

---

## G. Crop shade response — the riskiest research (Critical)

### D16 — Crop shade-response literature
**Why:** this decides how much yield each crop loses as GCR rises: the curve parameters **L_t** (the light threshold) and **k** (the slope), at low/central/high, plus an **evidence grade A–D** (spec §13). Every headline result depends on it.

**Scope:** the **20 largest annual crops by national cropped area**, covering every season they're grown in. Confirmed from D10 on 2026-11-07 (Q-04; `06_crops/area_production_yield/top20_national.csv`, column `research_list`). Perennial tree crops (mango, coconut) are excluded because panels cannot go over a mature orchard or plantation:
- cereals: rice, wheat, maize, bajra, jowar
- pulses: gram (chickpea), tur (pigeon pea), moong, urad, lentil
- oilseeds: soybean, mustard, groundnut, sesame
- fibre, sugar and gum: cotton, sugarcane, guar
- horticulture: potato, onion, cumin
- optional extras outside the 20, often good shade candidates: tomato (29th by area), ragi, leafy vegetables, turmeric, ginger

**Kinds of study to include, in order of value:**
1. Agrivoltaic field trials in India (e.g. ICAR-CAZRI Jodhpur and other Indian APV pilots).
2. Indian shade-net and agroforestry or intercropping shading trials.
3. International agrivoltaic trials in comparable climates (arid, semi-arid, tropical, sub-tropical).
4. Meta-analyses and reviews, for cross-checks and gap-filling (e.g. Weselek et al. 2019 and Laub et al. 2022 in *Agronomy for Sustainable Development*; verify the citations).

**Where to search:**
- Scopus, Web of Science and Google Scholar.
- **KrishiKosh** (ICAR's repository of theses).
- *Indian Journal of Agricultural Sciences* and *Indian Journal of Agronomy*.
- *Agrivoltaics World Conference* proceedings.
- Fraunhofer ISE reports.

Search terms: "agrivoltaic", "agrophotovoltaic", "shade net", "shading", "light reduction", "PAR", "yield", plus each crop name.

**Extract one row per treatment (template: `09_crop_shade_response/extraction/extraction_template.csv`):**
- *Study:* study_id, citation, DOI/URL, peer reviewed (Y/N), country, state/region, latitude, longitude, Köppen climate.
- *Crop and setting:* crop, variety, season, year(s), irrigated or rainfed.
- *Shade:* shading method (APV, shade net, agroforestry, other); for APV, the structure type, clearance height, GCR or row spacing, and module type.
- *Light:* **shade level, or measured light fraction (PAR or GHI relative to open field)**, and the measurement method.
- *Yield:* control yield, treatment yield, **relative yield** (treatment ÷ control), unit, and SD or SE and n if reported.
- *Other:* quality notes (e.g. grain filling, size, sugar), water-use notes, author caveats.

**Steps after extraction (spec §13.2):**
1. Fit `(L_t, k)` for each study.
2. Pool across studies: central = weighted median; low and high = the spread between studies.
3. Assign a grade:
   - **A:** ≥ 2 Indian field studies in comparable climates.
   - **B:** 1 Indian study, or ≥ 2 international studies in comparable climates.
   - **C:** 1 international study, or a well-supported extension from a closely related crop.
   - **D:** expert assumption only.

**Done when (spec §7.3):**
- All top-20 crops have parameters.
- The **top 10 are grade B or better** and the rest grade C or better.
- Every parameter has citations, and the fitted record sits in `09_crop_shade_response/parameters/`.

**Copyright:** keep paper PDFs **local only**. Research PDFs are git-ignored; commit only the citation and extracted data.

---

## H. Validation

### D17 — Field-trial observations for yield validation (Critical)
**Why:** proves the crop model's predictions are within **±15 percentage points** of observed relative yield for ≥ 80% of data points (spec §7.3, §13.4).

**Collect:**
- A **held-out set** of (light fraction, relative yield) observations from Indian studies, **not used to fit D16**. Aim for ≥ 30 points across ≥ 8 crops.
- Plus any reported APV pilot outcomes: crop, season, structure, GCR, yield vs. control, energy yield.

**Sources:** the same as D16, split at random or by study **before** fitting.

**Done when:** the hold-out set is frozen, its split is documented, and a validation report is written.

### D18 — Energy reference values (High)
**Why:** energy validation. pvlib must be within ±3% of PySAM, and within ±7% of Global Solar Atlas PV output.

**Collect:**
- Global Solar Atlas PVOUT for 10 sample districts covering different climates.
- **Measured generation from operating Indian plants where available**: KUSUM-A plants, rooftop or ground-mount plants, CUF reported by SECI or state agencies.

**Done when:** 10 districts have reference values, and at least 3 have measured plant data if obtainable.

---

## I. Finance and policy

### D19 — PM-KUSUM rules and state tariffs (Critical)
**Why:** finance defaults and the plant-size check (REQ-FIN-01, REQ-FIN-04).

**Collect:**
- MNRE PM-KUSUM guidelines (latest): Component A eligibility, **plant size 0.5–2 MW**, the substation-distance rule, the performance-based incentive to the DISCOM, the PPA term, and deadlines and extensions.
- **State-wise KUSUM-A tariffs (₹/kWh)**: the SERC order or tender result, the date, and whether a tariff is levelised or fixed. Note any state top-ups.
- Related state schemes, e.g. Maharashtra's Mukhyamantri Saur Krushi Vahini Yojana (solar on agricultural feeders, with lease payments to farmers), and any state agrivoltaic pilot policies.

**Candidate sources:** MNRE notifications; SERC tariff orders (MERC, RERC, GERC, etc.); state renewable energy agency tenders.

**Done when:**
- Every major state has a tariff with its source and date.
- States with no tariff are flagged to fall back on the national benchmark.

### D20 — CAPEX and O&M benchmarks (Critical)
**Why:** finance defaults. The low and high cases are ±10% around these.

**Collect, separately for ground-mount and APV:**
- **CAPEX per kWp** for ground-mount (fixed tilt), **elevated APV** (2.5–4 m clearance), single-axis tracker and vertical bifacial.
- **O&M per kWp per year**, with the escalation rate.
- Cost of grid interconnection at small scale (0.5–2 MW).
- Module, inverter and structure cost breakdown where available.
- The year of each figure, and the source type (tender, report, vendor quote).

**Candidate sources:** CERC/SERC capital-cost orders; recent SECI and state tender results; MNRE benchmark costs; industry reports (e.g. Mercom, Bridge to India); vendor quotes for elevated structures.

**Done when:** each structure preset has a central CAPEX and O&M figure with its year and source, plus a stated range.

### D21 — Lending, tax and depreciation (High)
**Why:** the financing section of KUSUM-A, and the Advanced panel (P1).

**Collect:**
- **Loan terms** for KUSUM-A or farm-solar loans: lender, interest rate, tenor, moratorium, debt share and collateral, from NABARD, public-sector banks and RRBs.
- Whether these loans count as **priority-sector lending**.
- **Income-tax treatment**: depreciation rate for solar (WDV) and the additional-depreciation rules in force; tax treatment for individuals, FPOs (producer companies), cooperatives and companies; MAT applicability.
- The discount rate convention for farmer-facing NPV.

**Candidate sources:** NABARD circulars; bank scheme pages; the Income Tax Act depreciation schedule (current year); RBI priority-sector guidelines.

**Done when:** default loan terms and tax rules are recorded with their dates. This also settles the open "check WDV rate" item in the spec.

### D22 — Land lease benchmarks (High)
**Why:** the lease model's default lease and the plausibility checks on the maximum affordable lease.

**Collect:**
- Observed **lease rents (₹/acre/year) and annual escalation** for solar on farmland: KUSUM-A developer arrangements, state schemes (e.g. Maharashtra's), and private agreements reported in the press or tenders.
- Local **agricultural land rental rates** (₹/acre/year) for comparison, where available.
- The lease term in years.

**Done when:** at least 5 states have lease benchmarks with their source and year.

### D23 — Yield-limit policy and international APV standards (High)
**Why:** the draft policy line (REQ-POL-01), the Method page, and open questions Q-01 to Q-03.

**Collect:**
- **The Indian draft yield-retention proposal**: wording, the body proposing it, the date, and above all *how retention is measured* (per acre of land or per cropped area; per season or per year) and *against what baseline*. Answering this settles Q-02 and Q-03.
- **International references**: Germany's DIN SPEC 91434, Japan's MAFF rules on farmland conversion for solar sharing (≥ 80% of local average yield), and the French, Italian and US state frameworks, for the Method page.
- Any MNRE or state agrivoltaic guideline or pilot scheme in India.

**Done when:** the Indian draft is documented with its measurement definition, and the international references are summarised with citations.

### D24 — Structure and module technology (High)
**Why:** the structure presets (REQ-MOD-02), `a_farm`, module efficiency and bifaciality used in physics.

**Collect, for each structure type** (elevated fixed-tilt at 2.5 / 3 / 4 m, single-axis tracker at 2 heights, vertical bifacial east–west):
- Typical tilt, row pitch range, module height and width, and post spacing.
- **Farmable fraction `a_farm`**: the area lost to posts, inverter pads and access tracks.
- Whether machinery can pass (tractor clearance and width).

**Modules:**
- Mainstream monofacial and bifacial modules in India: efficiency, **bifaciality factor**, temperature coefficient, dimensions. Take these from datasheets of ALMM-listed manufacturers.

**Done when:** every preset has documented geometry, `a_farm` and module parameters with their sources.

### D25 — Stakeholder interviews and policymaker notes (High)
**Why:** answers Q-01 to Q-03, checks the tool's assumptions, and supplies the qualitative trust metric (spec §7.2: ≥ 6 of 8 interviewees).

**Collect:**
- Notes from policymaker conversations (date, body, role; no personal contact data in the repo).
- **≥ 8 user interviews** across FPOs, NGOs, EPCs and consultants. For each: their current decision process, the numbers they need, their reaction to ranges, and their trust in the sources.

**Format:** one Markdown file per conversation, using `13_stakeholder_notes/interview_template.md`.

**Done when:** Q-02 and Q-03 are answered, and 8 interviews are logged.

---

## Cross-cutting rules for every dataset

1. **Provenance first.** Each dataset folder gets a `SOURCE.md` (copied from `_templates/SOURCE.md`) **before** any processing: publisher, URL, access date, version/year, licence, citation, coverage, resolution, caveats.
2. **Keep raw and derived data separate.** Put downloads in that folder's `raw/` (git-ignored, because the files are large). Put small hand-made tables (CSV) and notes next to `SOURCE.md`; those are committed.
3. **Join on LGD codes**, never on district names. Record every name-to-code mapping you make by hand.
4. **Units and years are explicit** in column names or the README (e.g. `yield_kg_per_ha`, `cost_inr_per_ha_2023`).
5. **Licence check** before anything is published. Record "OK / restricted / unknown" in `SOURCE.md` (open question Q-05).
6. **No personal data** in the repo: no farmer names, phone numbers or exact plot locations.
7. **Copyrighted papers** stay local. Commit citations and extracted numbers, not PDFs.

## Suggested order of work
1. **D00 and D06** (the district keys and cropland mask are the foundation), then **D10 and D11**, which decide the top-20 crop list.
2. **D16 and D17** (crop shade response and the validation hold-out set). This is the longest and riskiest work, so start it in parallel as early as possible.
3. **D19, D20, D23 and D25** (tariffs, costs, the policy definition, interviews), so `apv_core`'s defaults and Q-02/Q-03 can be finalised.
4. **D14 and D18** (solar and the energy references) ahead of the pipeline's physics build.
5. The rest (D01–D05, D07–D09, D12–D13, D15, D21, D22, D24) as the pipeline needs them.
