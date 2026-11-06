# AgriPV District Modeller — Design Spec

> **Superseded** by [`2026-11-06-agripv-lab-product-spec.md`](2026-11-06-agripv-lab-product-spec.md). The main changes: it's now a knowledge tool with range outputs; GCR runs 0.00–0.50; the draft policy limit is ≥ 80% retention as an editable reference line; crop parameters carry evidence grades; bank-grade metrics move to Advanced. Kept for history.

- **Date:** 2026-11-06
- **Status:** Approved in brainstorming; awaiting written-spec review
- **Working name:** AgriPV Lab (placeholder; final name open)
- **Product record:** [`PRODUCT.md`](../../../PRODUCT.md)
- **Chosen visual direction sketch:** [`.impeccable/mocks/decision/model-pick.html`](../../../.impeccable/mocks/decision/model-pick.html) (Toposheet)

---

## 1. Summary

A web app for checking whether agrivoltaics (APV) suits an **Indian district**, and how to design it there. It combines six district-level data layers (agro-climate, soil, elevation, groundwater and irrigation, crops and crop economics, solar resource) with a techno-economic model in the spirit of NREL's ADAM, rebuilt for Indian conditions. The core output is the **trade-off between farm income and energy income per acre as ground coverage ratio (GCR) changes**, together with the **land equivalent ratio (LER)** and the cash flows for the two business models. Each session ends in a client-ready PDF and Excel report.

### Why not use ADAM directly
ADAM (OpenEI/InSPIRE) is a US-tuned web form with no public API: US federal and state tax, MACRS depreciation, NSRDB weather, $/acre. Its calculation engine, NREL's SAM, is open source, but its assumptions don't carry over to India. The saltysaguaro *agrivoltaic-experiment-designer* is a shading/PAR simulator under a proprietary licence. We use it as a source of ideas only and reuse none of its code.

## 2. Users and success

- **Primary users:** FPOs, NGOs, EPC firms and consulting firms in India, working desktop-first while preparing proposals, feasibility notes, DPR inputs and board or bank discussions. Farmers are reached through these users, not directly.
- **Secondary purpose:** an academic and portfolio project, so the method must be fully traceable.
- **Typical session:** starts from a **known district** and ends with a **client-ready report**.
- **Success:** in under 10 minutes a user can pick a district, run both business models, find a defensible GCR and structure, and export a report where every number shows its source, year and method.

## 3. Scope

### In scope (v1)
- All of India at **district level** (~780 districts, keyed by LGD code).
- The six data layers, aggregated to districts, with source records (provenance) and data-quality flags.
- Pre-computed physics for a preset grid of structure configurations.
- Live crop response and finance for **PM-KUSUM Component A** (farmer/FPO owner-operator) and **land lease** (developer-owned).
- GCR sweep, LER, economic ratio, yield-retention limit, optimum, uncertainty band.
- District screening with filters; scenario comparison (up to 3); shareable URLs.
- PDF report (print-optimised page) and Excel export; methodology and sources pages.
- English UI, with all strings in translation files.

### Non-goals (v1)
- Site-level analysis: custom geometry, substation distance, geotechnical conditions, parcel boundaries.
- PM-KUSUM Component C, captive use, C&I/open-access sale.
- User accounts, server-side scenario storage, multi-user collaboration.
- Hindi or regional-language translations (structure ready, content later).
- A composite "suitability score" with hidden weights (filters only).

## 4. Architecture and deployment

**Approach:** a Python core, a FastAPI API and a lightweight React frontend in one GitHub repo, deployed on Vercel.

**Key decision: physics offline, economics live.**
- *Offline (pipeline):* for every district and every preset configuration, simulate monthly AC energy per kWp and monthly ground light fraction. The output is small (~10 MB uncompressed for all of India) and is bundled with the API function.
- *Live (API):* crop response and finance are cheap numpy calculations. There is no pvlib at runtime, so the function stays small and quick to start.
- *Trade-off accepted:* users choose from preset structure configurations rather than entering any geometry they like. That's appropriate for district-level screening.

**One sweep per change of inputs:** `POST /api/sweep` returns results for every GCR value. The GCR slider reads results already loaded in the browser, so it responds instantly without extra calls.

**Deployment:**
- The frontend is a static Vite build served from Vercel's CDN. District boundaries and the context table are static files on the CDN.
- The API is a FastAPI app on Vercel's Python runtime, bundled with `physics.parquet`, the crop parameters and the finance defaults.
- **Hosting caveat:** Vercel's Hobby plan is limited to personal, non-commercial use. Commercial use by EPCs or consultancies means moving to Pro, which needs no code changes.

### Repo layout
```
pipeline/    Offline Python: fetch → clean → aggregate to districts → simulate physics → build artefacts
apv_core/    Python package: crop response, LER, KUSUM-A & lease finance, GCR sweep (pure, unit-tested)
api/         FastAPI app (Vercel Python runtime); imports apv_core; reads bundled artefacts
web/         Vite + React + TypeScript; MapLibre GL; charts; report page
data/        Versioned build outputs (see §5.4)
docs/        Methodology, sources, specs
```

### Data flow
1. Run the pipeline (locally or in GitHub Actions). It validates the data and writes versioned artefacts to `data/`, which are copied into `web/public/data/` and `api/`.
2. The frontend loads boundaries and `districts` context from the CDN.
3. The user picks a district and enters inputs. The frontend calls `POST /api/sweep` and receives the full GCR sweep, cash flows and warnings.
4. The report page renders from the same response. Excel comes from `POST /api/export/xlsx`.

## 5. Data layers and pipeline

### 5.1 District list and boundaries
- One canonical district list keyed by **LGD code**, with recent simplified boundaries.
- Sources using older boundaries (e.g. the ICRISAT district database, some DES series) are mapped through a **lookup table between old and new districts**. Mapped values set the `boundary_mapped` flag.

### 5.2 Cropland weighting
Before averaging rasters over a district, mask them to cropland using ESA WorldCover. Every raster statistic describes **cropland in that district**, not the whole district.

### 5.3 Layers (sources are candidates; licences and access to be confirmed in planning)

| Layer | Candidate source | Fields stored per district |
|---|---|---|
| Agro-climate | Planning Commission 15 agro-climatic zones; NBSS&LUP agro-ecological sub-regions; IMD gridded rainfall (0.25°) and temperature | zone; sub-region (by area majority); normal kharif, rabi and annual rainfall; days above 40 °C; aridity index |
| Soil | ISRIC SoilGrids 250 m; NBSS&LUP qualitative classes | dominant texture; mean pH, organic carbon, depth to bedrock (cropland-weighted) |
| Elevation | Copernicus GLO-30 DEM | mean, P10 and P90 elevation; mean slope; % of cropland below 5° slope |
| Groundwater / irrigation | CGWB Dynamic Ground Water Resources (latest assessment); DES land-use statistics; Minor Irrigation Census | stage of extraction %; share of assessment units over-exploited, critical, semi-critical or safe; % net irrigated area; irrigation mix by source |
| Crops | DES district area, production and yield (recent 5-year average); ICRISAT district database for gaps | top crops by area per season (kharif, rabi, zaid), with yield per hectare |
| Crop economics | CACP cost-of-cultivation (state level); MSP; Agmarknet mandi prices | per crop: price per quintal, cost per acre (state-level fallback flagged) |
| Solar | PVGIS typical meteorological year (TMY) at the district's cropland centroid (drives physics); Global Solar Atlas (map + cross-check) | annual and monthly GHI; PV output per kWp; hourly TMY (offline only) |

Soil Health Card data is left out of v1 because it can't be obtained consistently.

### 5.4 Artefacts (in `data/`, versioned)
- `districts.parquet` and `districts.json`: one row per district, ~100 columns, with data-quality flags.
- `boundaries.geojson` (simplified) or `.pmtiles`.
- `physics.parquet`: see §6.1.
- `crops.json`: crop list with season, shade-tolerance group and response parameters (low, central, high) with citations.
- `finance_defaults.json`: state KUSUM-A tariffs, CAPEX and O&M benchmarks, loan terms, tax and depreciation defaults, each with source and date.
- `sources.json`: provenance for every field (source, data year, method, licence, URL).
- `manifest.json`: data version, build date, checksums, coverage by layer.

### 5.5 Data-quality flags (per district, per field group)
`missing`, `state_fallback`, `boundary_mapped`, `imputed`. These flags appear in the UI and the report.

## 6. Model chain

The chain runs for every district × configuration × GCR value (0.10 to 0.60 in steps of 0.05, so 11 values).

### 6.1 Physics (offline, pvlib)
- **Configuration grid:**
  - Elevated fixed-tilt: 3 clearance heights × mono or bifacial
  - Single-axis tracker: 2 hub heights × mono or bifacial
  - Vertical bifacial (east–west)
  - All of the above × 11 GCR values, giving about 120 configurations per district.
- **Energy:** pvlib simulation driven by the district TMY, with standard losses and bifacial gain for bifacial modules. Stored as monthly AC energy per kWp, `E[m]`.
- **Ground light:** a 2-D view-factor model across the row pitch (infinite-sheds geometry). It covers direct-beam shadow plus diffuse light from the visible sky, on a ground line across the row, averaged over the cultivable band. Stored as the monthly ground light fraction `L[m]`, relative to open field. PAR is taken as a fixed fraction of shortwave.
- For the reference conventional PV plant used in LER: ground-mounted fixed tilt at GCR ≈ 0.45 in the same district (stored separately).

### 6.2 Land use per acre
- `kWp_per_acre = GCR × 4046.86 m² × η_module × 1 kW/m²` (vertical bifacial uses a definition based on row pitch, documented in the method pages).
- `a_farm`: the fraction of the acre that can still be farmed after posts, inverter pads and access tracks. Each structure type has a default, and the user can change it.

### 6.3 Crop shade response
- **"Hockey-stick" curve per crop:** `Y_rel = 1` if `L ≥ L_t`, else `1 − k × (L_t − L)`, clipped to [0, 1].
- `L` is the ground light fraction **averaged over that crop's season months**: kharif June–October, rabi November–March, zaid March–June.
- Parameters `(L_t, k)` come from a literature review. Crops are grouped tolerant, neutral or sensitive, with low, central and high values, and every parameter is cited.
- **Heat-relief uplift** (optional, **off by default**): a capped positive adjustment for districts with many days above 40 °C, clearly labelled and cited.

### 6.4 Farm income per acre
`I_farm = Σ_season [ Y_base × Y_rel × a_farm × price − cost × a_farm × (1 + p_apv) ]`
- The rotation (kharif + rabi + optional zaid) defaults to the district's main crops.
- `p_apv` is an editable allowance for the drag on farm operations from working around the structure. It defaults to a small value.
- Baseline (no APV): `Y_rel = 1`, `a_farm = 1`, `p_apv = 0`.

### 6.5 LER and economic ratio
- `LER = agri_term + energy_term`
  - `agri_term`: per season, `a_farm × Y_rel`. The headline value weights seasons by baseline crop revenue, and the per-season values are reported too.
  - `energy_term = APV energy per acre ÷ reference-PV energy per acre`.
- `economic_ratio = (I_farm + I_energy) ÷ baseline I_farm`.

### 6.6 Finance (25 years, annual; real and nominal handled explicitly)
- **Common inputs:**
  - CAPEX per kWp, with an elevated-structure premium over ground-mount
  - O&M per kWp per year, with escalation
  - degradation and availability
  - state KUSUM-A tariff (fixed for the contract term; default for each state, editable)
  - debt share, interest rate and loan tenor
  - tax rate and WDV depreciation (rate to be checked against current Income Tax rules)
  - crop price and cost inflation; discount rate
- **KUSUM-A (owner):** cash flow = energy revenue + farm income − O&M − debt service − tax. Outputs: equity IRR, project IRR, NPV, payback, minimum and average DSCR, LCOE.
  - Warns when the plant size implied by land and GCR is outside the scheme's 0.5–2 MW range.
- **Lease (developer-owned):**
  - Developer cash flows give project and equity IRR.
  - The farmer receives lease plus farm income on `a_farm`.
  - **Maximum affordable lease at the developer's target IRR** has a closed form: `lease_max = NPV_without_lease(target) ÷ escalating annuity factor`. It is cross-checked numerically in tests.

### 6.7 Sweep and optimum
- For each GCR: farm, energy and total income per acre; LER; economic ratio; financial metrics.
- **Objective (user-selected):** total income per acre, farmer income, LER, or equity IRR.
- **Yield-retention limit:** presets are DIN SPEC 91434 (≥ 66%) and the Japanese rule (≥ 80%), editable. The optimum is the best feasible GCR.
- **Uncertainty band:** results under the low and high crop-response parameters.

## 7. API contract (v1)

| Method & path | Purpose |
|---|---|
| `GET /api/meta` | data version, build date, coverage, available configurations, crop list |
| `GET /api/district/{lgd}` | full context row + flags + insights for one district (also available statically) |
| `POST /api/sweep` | inputs: district, business model, configuration, rotation, finance inputs, retention limit, objective → per-GCR results (both models' metrics as applicable), optimum, uncertainty band, yearly cash flows at the optimum and the selected GCR, `warnings[]` |
| `POST /api/export/xlsx` | same inputs → Excel workbook of inputs, assumptions, cash flows, sources |

- Requests and responses are Pydantic models. The OpenAPI schema generates the frontend's TypeScript types.
- Every response carries `data_version`.

## 8. UI and user flow (Toposheet direction)

**Mode:** Operate (a working tool). Familiar patterns and standard controls come first; the visual style shows through type, palette, density and one signature element. The build works directly in code; no image mock-ups are made first.

### 8.1 Visual world
- **Type:** Barlow Condensed for sheet titles and map labels; Barlow for the interface. Tabular figures throughout, with ₹ grouped in lakh and crore (e.g. ₹14,57,000).
- **Palette (each colour has a job):**
  - off-white sheet ground (not cream), black ink
  - contour brown for slope and terrain
  - water blue for groundwater and the **energy** series
  - vegetation green for cropland and the **farm** series
  - black for **LER**
  - survey red **only** for the selected point and the optimum
  - warnings use a separate ochre plus an icon, so red keeps one meaning
- **Density:** fine hairlines, small labels, compact panels.
- **Signature element:**
  - Every map and chart sits inside a **sheet margin with grid-reference ticks**.
  - The optimum GCR is marked as a **survey reference point** (red triangle), on the chart, in the results list and in the report.
  - The layer legend is a **conventional-signs panel**, the key printed on survey sheets.

### 8.2 Flow (searching for a district comes first)
1. **Home:** a large "District or LGD code" search over an India sheet, with recent scenarios below it. **Find districts** (screening) is a secondary tab: map plus filters (e.g. GHI above X, under Y% blocks over-exploited, Z% of cropland below 5°) and a sortable results list.
2. **District sheet (context):** the district map leads, inside graticule margins.
   - The conventional-signs panel turns layers on and off.
   - The six layers appear as compact margin panels with data-quality badges and links to sources.
   - **Context insights:** rule-based, from one cited YAML rules file that domain experts can edit.
   - The main action is **Model this district**.
3. **Model:** the same sheet frame with the map shrunk to a **locator inset**, so the GCR trade-off takes the sheet body.
   - **Left:** steps in order (business model → structure → crop rotation → finance, pre-filled with state defaults → yield-retention preset). Only the current step is open; finished steps collapse to one-line summaries.
   - **Centre:**
     - The chart shows farm share (green) and energy share (blue) across GCR, with the LER line, the retention-limit line, the survey-point optimum and the uncertainty band.
     - **Dragging the GCR slider updates everything live**, with no Run button.
     - Kharif, rabi and zaid panels **share one scale**.
   - **Right:** results for the selected GCR: LER, farm retention, ₹ per acre, IRRs, DSCR, payback, LCOE, plant size against KUSUM limits, maximum affordable lease.
   - **Below the visible screen:** the yearly cash-flow table and a data table version of the chart.
4. **Compare:** up to 3 saved scenarios side by side. Scenarios are kept in the browser, and every scenario has a shareable URL that encodes its inputs plus `data_version`.
5. **Report:** a print-ready sheet whose title block works like a toposheet's: district, data edition (pipeline version), legend of sources, all assumptions, results, charts and warnings. It exports to PDF via a print stylesheet, and Excel comes from the API.
6. **Method and sources:** equations, parameter tables, sources, licences, known limitations.

### 8.3 States
- **Loading:** the previous result stays visible but dimmed.
- **API error:** retry, with inputs kept.
- **Cold start:** the first sweep may be slow, so show progress inside the chart frame.
- **Missing district data:** the panel says what is missing and why. If crop data is missing, the user can enter it by hand.
- **No GCR meets the retention limit:** explain this and suggest a different structure (e.g. vertical bifacial).
- **Plant size outside the KUSUM range:** warning.
- Long district names; empty compare view; first visit with no recent scenarios.

### 8.4 Range of data to design for
About 780 districts; 1–3 seasons; GCR 0.10–0.60; ₹ values from thousands to crores.

### 8.5 Accessibility and screen sizes
- Colour is never the only signal; series also differ by line style.
- Text contrast is at least 4.5:1.
- The GCR slider works from the keyboard.
- Every chart has a data table version.
- Browser defaults (focus rings, text selection, tabular numerals, scrollbars) are styled to match the palette.
- **Desktop-first** (1280–1600 px). On a tablet, the margin panels stack below the sheet. On a phone, the app is a read-only results and report view.

## 9. Error handling

### Pipeline
- Every source is checked for structure, row counts and plausible ranges (e.g. GHI 3.5–7 kWh/m²/day, percentages 0–100, crop yields within limits set per crop).
- If a layer covers fewer districts than its threshold, the build fails. Gaps for individual districts become flags.
- Builds can be safely re-run; raw downloads are cached locally and not committed; artefacts are versioned with checksums.

### API
- Pydantic validation; a 422 response names the field and the problem, and the UI shows it next to that input.
- Unknown district or missing configuration gets a clear 404 or 422, never a 500.
- Numerical edge cases return `null` **plus a reason**, never a crash or `NaN`:
  - "IRR undefined (no sign change)"
  - "Not viable at target IRR" (negative lease)
  - "No GCR meets the retention limit"
- **Warnings are part of the response:** KUSUM size, state-level data used, crop response pushed past the range of the literature, heat-relief uplift on. Every warning appears in the UI and the report.

### Frontend
- Previous results are kept while recalculating; network and timeout errors offer a retry and keep all inputs.
- Opening a scenario URL built on an older `data_version` shows a notice that results may differ.

## 10. Testing

- **`apv_core` (pytest):**
  - Finance against hand-worked reference cases (NPV, IRR, DSCR).
  - The closed-form maximum lease against a numerical search.
  - LER arithmetic.
  - Crop-response curve properties: never above 100%, and never rising as light falls.
- **Property tests (Hypothesis):** a higher tariff never lowers IRR; a higher GCR never raises the farm share; more debt changes DSCR in the expected direction.
- **Physics validation (pipeline):**
  - pvlib energy vs PySAM for ~10 sample districts, within ±3%.
  - Annual PV output vs Global Solar Atlas.
  - Ground-light fraction vs published agrivoltaic results where any exist.
- **Data tests:** structure, range and coverage checks; snapshot tests on a few well-known districts.
- **API:** contract tests with FastAPI TestClient; OpenAPI-generated TypeScript types checked in CI.
- **Frontend:**
  - Vitest for lakh/crore formatting and screen states.
  - Playwright end-to-end (search → model → export) against Vercel preview deployments at 1440 px and 390 px.
- **CI (GitHub Actions):** pytest, type checks, Vitest and Playwright on every pull request; pipeline validation when pipeline code changes.

## 11. Delivery: sub-projects and order

The system is big enough that each sub-project gets **its own implementation plan**, written in this order:

1. **`apv_core`:** crop response, LER, KUSUM-A and lease finance, sweep and optimum, built and tested against synthetic physics and parameter fixtures. This is the scientific and financial heart, and it can be tested without any real data.
2. **`pipeline`:** district list and boundaries, the six layers, cropland weighting, physics simulation, validation, artefacts. Includes the literature review for crop shade-response parameters and the sourcing of state KUSUM tariffs.
3. **`api`:** FastAPI on Vercel, bundled artefacts, Excel export, OpenAPI types.
4. **`web`:** Toposheet UI — home and screening, district sheet, model, compare, report, method pages.

Steps 1 and 2 can run in parallel once the artefact formats (§5.4, §6.1) are fixed. Steps 3 and 4 depend on both.

## 12. Risks and open decisions

| Item | Status / mitigation |
|---|---|
| Crop shade-response parameters are uncertain and differ between studies | Cited low, central and high values; uncertainty band; method page states the limits |
| Crop economics are the weakest layer (state-level costs, noisy mandi prices) | Data-quality flags; every field editable; state fallback flagged |
| Licences and access terms for IMD gridded data, Agmarknet and others | Check each one while planning the pipeline; leave out or replace any that don't allow this use |
| District boundary changes | LGD-keyed list + old-to-new district lookup + `boundary_mapped` flag |
| State KUSUM-A tariffs change over time | `finance_defaults.json` records the date and source of each tariff; tariffs are editable |
| WDV depreciation rate and tax treatment for FPOs and companies | Check current Income Tax rules during the `apv_core` plan |
| Vercel Hobby is non-commercial | Move to Pro before any commercial use |
| Product name | Open; "AgriPV Lab" is a placeholder |
