# Web app, first slice: the Model page — design

| | |
|---|---|
| **Date** | 2026-11-15 |
| **Status** | Draft for owner review |
| **Parent spec** | [`2026-11-06-agripv-lab-product-spec.md`](2026-11-06-agripv-lab-product-spec.md) (§8, §10, §11, §15) |
| **Builds on** | [`2026-11-14-live-physics-design.md`](2026-11-14-live-physics-design.md) (`apv_physics`, weather packs) and `apv_core` |

## 1. What this is

The first deployed version of AgriPV Lab. A user searches for a district, sets a panel layout, crops and
finance, and sees how farm income and energy income trade off across panel density, with ranges, against
the draft 80% yield line. It runs the live physics engine and the model core on Vercel.

It is a **preview**: crop shade parameters are draft, crop economics are state-level figures for 2021-22,
and loan terms are assumptions. The app says so on every page.

## 2. Decisions already made

| Decision | Choice | Why |
|---|---|---|
| First slice | The Model page, with search and a Sources page | It proves the riskiest part (live physics in a Vercel function) and is usable on its own |
| Data | What is in the repo today; research gaps come later | Owner decision, 2026-11-15 |
| Weather packs | Committed to the repo (40 MB) | Simplest route to Vercel; relies on the licence reading in `SOURCE_pvgis_tmy.md` |
| Stack | Vite + React + TypeScript; FastAPI on Vercel's Python runtime | Parent spec §15.1 |
| Visual direction | Toposheet (parent spec §10.1) | Chosen earlier; sketch in `.impeccable/mocks/decision/model-pick.html` |

## 3. Scope

**In scope**

- `pipeline.appdata`: an offline script that builds the app's JSON data from files already in the repo.
- `api/`: a FastAPI app with four endpoints.
- `web/`: Home (district search), Model page with a first-visit tour, Sources page.
- Deployment on Vercel from this repo, with a preview per branch.
- Tests and CI for all three.

**Out of scope** (later slices, each with its own design)

- The India map, district boundaries and the district context sheet.
- Compare, the Estimate Sheet and PDF, saved-scenario lists.
- Learn pages and the full Method page.
- Advanced finance, Excel export, district screening, Hindi.
- Default crop rotation per district and district-level yields (research gap D10).

## 4. Architecture

```
offline                                 Vercel (one project, one domain)
-------                                 --------------------------------
research/*.csv ──► pipeline.appdata ──► data/app/*.json ──┐
data/weather/*.npz (committed) ───────────────────────────┤
                                                          ▼
web/ (static, CDN)  ── fetch /api/* ──►  api/ (FastAPI function)
  Home, Model, Sources                     load data → apv_physics.simulate → apv_core.run_sweep
```

- **`pipeline/src/pipeline/appdata/`** (offline): reads research CSVs and `data/weather/index.json`, writes
  `data/app/*.json`. Committed outputs; rebuilt by hand when research data changes.
- **`api/`**: FastAPI. Imports `apv_physics` and `apv_core` from the repo, reads `data/app/` and
  `data/weather/`. No database, no accounts, no state between requests except an in-memory cache.
- **`web/`**: a static single-page app. All calculation happens in the API.
- `apv_core` and `apv_physics` do not change.

## 5. App data (`data/app/`)

Built by `python -m pipeline.appdata.build_app_data <repo_root>`. Every default value carries where it came
from, so the interface can show it.

| File | Content | Built from |
|---|---|---|
| `districts.json` | 785 districts: `id` (the weather-file stem, e.g. `107_jodhpur`), LGD code, name, state, latitude, longitude, elevation, optimum tilt | `data/weather/index.json` |
| `crops.json` | The 20 research crops: id, name, seasons, shade parameters (pessimistic, central, optimistic `L_t` and `k`), evidence grade, number of studies and Indian studies, notes, citations, `selectable` and a reason when not | `crop_parameters_draft.csv`, `bibliography.csv` |
| `crop_economics.json` | Per state and crop: yield (quintals per acre), price (₹ per quintal), cost of cultivation (₹ per acre), year, and `basis`; plus the example crops per state | DES cost of cultivation (`idp_des_cost_of_cultivation_1996-2022.csv`, ODC-By) |
| `finance_defaults.json` | Tariff per state with its order and status; cost and O&M per structure preset (central, low, high); loan and other terms | `kusum_a_state_tariffs.csv`, `capex_om_benchmarks.csv`, `lease_benchmarks.csv` |
| `structures.json` | The 6 agrivoltaic presets as layouts: kind, tilt rule, direction, height, row width, tracker limit, unfarmed strip, module, farmable fraction (central, low, high), cost multiplier, machinery note | `structure_presets.csv`, `module_parameters.csv` |
| `sources.json` | Attribution text, licence and link for every dataset the app shows | Source cards |
| `manifest.json` | Data version, build date, row counts, SHA-256 of each file | — |

Rules:

- **Crop economics.** Yield = `derived_yield` ÷ 2.4711 (hectares to acres). Price = `main_product_value` ÷
  `derived_yield`. Cost = `cul_cost_a2fl` (paid-out costs plus family labour) ÷ 2.4711. The latest year with data
  is used for each state and crop (2021-22 for 187 pairs across 19 states). `basis` is `state` where the
  state has the crop; `national_median` (the median across states) where it does not; `none` where no state
  has it (guar and cumin), in which case the user must enter values.
- **Example crops.** For each state, the kharif crop and the rabi crop with the most holdings in the
  cost-of-cultivation sample (`num_holdings_sample`) among selectable crops with state economics; the rabi
  pick may not repeat the kharif crop. For example: Rajasthan bajra and wheat, Maharashtra soybean and gram,
  Punjab rice and wheat. States without data use the national pair, rice and wheat. They are examples to
  start from, not a claim about the district.
- **Crops that cannot be modelled yet.** Sugarcane is a whole-year crop and the model works by season, so it is
  listed but not selectable. Cumin (grade D) is listed but not selectable, per parent spec REQ-CRP.
- **Tariff.** The state's KUSUM-A tariff where one exists (11 states), otherwise the national fallback of
  ₹3.11/kWh with a `state_fallback` flag.
- **Loan and other terms.** Not researched yet (gap D21). The file carries placeholders marked
  `assumption`: debt share 70%, interest 10%, loan 15 years, discount rate 9%, panel degradation 0.5% a
  year, availability 99%, crop price inflation 5%, target IRR 12%, lease ₹40,000 per acre per year rising
  5% a year. The interface labels each as an assumption.
- **Custom heights.** Cost benchmarks exist for the preset heights only. For another height the cost
  multiplier is interpolated linearly between the presets of that structure type, held at the nearest
  preset's value outside their range, and flagged `outside_benchmark_range`.
- State names differ between sources ("ODISHA", "Odisha"); one normalising table in the script maps them.

## 6. API

FastAPI app, entrypoint `api/index.py` (`app`). All routes are under `/api`.

| Method and path | Purpose | Response |
|---|---|---|
| `GET /api/meta` | Everything the Model page needs once | Data version, preview notice, structure presets, layout limits, crops, seasons, policy default and range, finance assumptions |
| `GET /api/districts` | The search list | 785 entries: id, name, state |
| `GET /api/district/{id}` | One district's defaults | District details, optimum tilt, state tariff with source and flag, crop economics available in its state, the example crops |
| `POST /api/sweep` | Run the model | See below |
| `GET /api/health` | Liveness and data version | Status, number of weather packs, Python version, data version |

**`POST /api/sweep` request**

```json
{
  "district_id": "107_jodhpur",
  "business_model": "kusum_a",
  "layout": {
    "preset_id": "elevated_fixed_3m",
    "kind": "fixed", "tilt_deg": 25.0, "azimuth_deg": 180.0, "height_m": 3.0,
    "collector_width_m": 4.56, "max_angle_deg": 55.0, "unfarmed_strip_m": 1.0,
    "module": {"efficiency": 0.225, "bifaciality": 0.8, "temp_coeff_per_c": -0.003}
  },
  "a_farm": 0.92,
  "rotation": [
    {"season": "kharif", "crop_id": "bajra", "economics": null},
    {"season": "rabi", "crop_id": "wheat",
     "economics": {"yield_q_per_acre": 14.0, "price_per_q": 2275, "cost_per_acre": 16000}}
  ],
  "finance": {"tariff_per_kwh": 3.04, "capex_per_kwp": 39120},
  "policy_limit": 0.8,
  "retention_basis": "per_acre_of_land",
  "land_acres": null
}
```

- Only `district_id`, `business_model`, `layout.kind` and `rotation` are required. Anything left out takes the
  preset's or the state's default.
- `economics: null` means "use the state default"; the request fails with a clear message if there is none.
- `finance` holds overrides only.

**`POST /api/sweep` response**

- `gcr`: the 11 densities.
- `metrics`: for each headline metric, 11 values of `{low, central, high}`.
- `retention`: per season, 11 values of `{low, central, high}`; `retention_basis`.
- `light`: per season, mean light and light on the darkest tenth of the farmed ground, 11 values each.
- `clear_gap_m`: 11 values.
- `allowed_gcr`: `{low, central, high}`; `outside_policy`: 11 booleans.
- `baseline_farm_income`.
- `notices`: code, message, and the densities each applies to.
- `inputs_used`: every resolved input with its value, source label, year and flag, so the page can show
  what the numbers rest on.
- `data_version`, `engine_ms` (time spent in physics and model).

**Behaviour**

- Physics results are cached in memory by district and layout (64 entries). A change to crops, finance or
  policy reuses them.
- Errors: 404 for an unknown district; 422 with the field name for any invalid value, including the
  `ValueError`s that `apv_physics` and `apv_core` raise. Never a 500 with a stack trace (REQ-ERR-04).
- The OpenAPI schema is the contract. TypeScript types for the web app are generated from it.

## 7. Web app

The front-end brief below was confirmed by the owner on 2026-11-15 (worked through with the `impeccable`
skill's `shape` process). It replaces the first draft of this section.

### 7.1 Who arrives and what success is

An FPO officer, NGO analyst, EPC engineer or consultant at a desk, with one district already in mind, asking
whether agrivoltaics is worth discussing there. It is a working tool: finding things fast comes before
decoration. Success: within a minute of picking a district they can say how much more the land could
produce and where the draft 80% yield line cuts in, and every number they quote can be traced to a source.

### 7.2 Direction

- **Visual world: Toposheet** (parent spec §10.1; sketch `.impeccable/mocks/decision/model-pick.html`). It
  supplies four things only: type (Barlow Condensed for titles, Barlow for the interface, tabular figures,
  fonts served from the project), the palette, a fine-lined dense layout, and one signature. Layout,
  navigation and controls are standard web ones.
- **Signature.** The chart sits inside a survey-sheet frame whose margin ticks are the panel-density scale.
  A red survey triangle on that margin marks the chosen density, with a hairline up through the chart and
  the season panels. The same triangle heads the results panel.
- **Colour does jobs.** Sheet `#F3F3EE`, ink `#151515`, mute `#5A5A55`, line `#CFCFC6`; green `#5E8C3A` farm
  income; blue `#2B6CB0` energy income; black LER; red `#C0392B` the chosen density and nothing else; grey
  hatching beyond the draft limit; ochre for warnings; brown `#8A5A2B` reserved for terrain in later slices.

### 7.3 Pages

| Route | Content |
|---|---|
| `/` | A sheet frame with the product name, one sentence on what the tool does and a large search box, focused on arrival (type-ahead over district and state, keyboard operable). Below: recently opened districts (kept in the browser) and three examples to try. The preview notice. A link to Sources |
| `/model/:districtId` | The Model page (§7.4) |
| `/sources` | A reading page: each dataset with its attribution and licence; what is draft or assumed; a short account of the method with links to the specs |

**Top bar on every page:** product name; the open district as the active tab; Sources; a search box to switch
district; on the Model page, a "How to read this" button.

### 7.4 Model page

Three columns at 1200 px and wider: inputs rail, sheet, results panel.

**Worked result first.** Opening a district shows a result at once: the elevated 3 m fixed preset, PM-KUSUM A,
and two example crops, each tagged "Example crop, change it". The examples are the kharif and rabi crops
most often surveyed in that state's cost-of-cultivation data (§5). The selected density starts at the
highest allowed density, or 0.25 when there is none.

**Left rail: inputs.** Five sections, each collapsed to a one-line summary; one opens at a time. Each
pre-filled value carries a short source tag.

1. **Business model:** PM-KUSUM A or land lease.
2. **Structure:** six preset cards (a small section drawing, the default farmable fraction, a machinery
   note). "Edit layout" opens tilt and direction (or the tracker's turning limit), panel height, panels per
   row, and module specs, each with its limits. Next to height and row width: "Changes how even the light is
   and the gap between rows, not average light or energy." An edited preset is labelled "Custom layout".
3. **Crops:** one slot each for kharif, rabi and zaid; at least one must be filled. Each slot has a crop
   list with evidence-grade badges and three economics fields, pre-filled from the state, the national
   median or left empty, with a tag saying which.
4. **Finance:** tariff (state order or national fallback), cost per kWp and O&M (from the structure), loan
   terms and lease (assumptions), all editable. Optional plot size in acres, for the KUSUM size check.
5. **Policy line:** limit from 50% to 100% in steps of 5; "Measure yield against" per acre of land or per
   cropped area.

**Centre: the sheet.** A title block (district name in Barlow Condensed capitals, state, coordinates,
elevation, data version), then the chart, drawn as SVG.

- Horizontal axis: panel density (GCR) from 0 to 0.50, on the sheet's margin ticks.
- **LER** is the heaviest line (black), on the right axis.
- Left axis, ₹ per acre per year: farm income (green) and energy income (blue), each a central line with a
  low-to-high band.
- The first density at which any season falls below the policy limit is marked; the region beyond it has
  grey hatching and the label "Outside proposed limit (draft)".
- The chosen density: red survey triangle and hairline; a slider below the chart and the arrow keys move it
  in steps of 0.05.
- Below, on the same horizontal axis: one small panel per season showing yield kept with its band and the
  policy line, and mean light with the darkest-tenth light.
- A data table of the same numbers under the chart, for screen readers and for copying.

**Right: results at the chosen density.**

- **LER leads**, as the large figure with its range, and one plain line beneath it: "This acre produces as
  much as 1.45 acres used separately for farming and solar."
- The legend, styled as the sketch's "Conventional signs" panel.
- Then: farm income, energy income and total against open-field farming today, each as a range; yield kept
  per season; the allowed density range; kWp and kWh per acre; payback and project IRR (for lease: the
  farmer's lease income, the developer's IRR and the highest affordable lease); clear gap between rows;
  light evenness; warnings.

**Plain words.** Every term appears in plain language with the technical name beside it: "Panel density
(GCR)", "Land equivalent ratio (LER)", "Yield kept". Each result has a one-line meaning and a source tag
that opens where the number comes from.

**First-visit tour.** Five short steps: the chart, the density marker, the 80% line, changing crops, source
tags. It can be skipped, is remembered in the browser, and reopens from "How to read this". Focus moves with
each step and Escape closes it.

**Scenario in the address.** Every input is encoded in the URL query, so a copied link reproduces the
scenario. Defaults are left out to keep it short.

### 7.5 States

| State | Behaviour |
|---|---|
| Loading | The previous result stays, dimmed; a progress line runs inside the chart frame |
| Moving the density | Instant: every density arrived in one response |
| API error | Message with a Retry button; inputs are kept |
| Invalid input | The field shows the message from the API |
| No economics for a crop | The slot asks for the three values before running |
| No allowed density | "No panel density in this range keeps [crop] at or above 80% yield" |
| Low-evidence crop | Ochre icon and note beside the crop and in the warnings |
| KUSUM size out of range | Warning naming the densities, when a plot size is given |
| Unknown district in the address | A not-found page with the search box |

### 7.6 Interaction and layout rules

- Numbers: Indian digit grouping and lakh / crore for large rupee amounts, through one formatting function.
  Ranges are written with the central value first, then "low – high".
- Motion is restrained: chart lines ease to a new result in about 200 ms; nothing else animates; reduced
  motion is honoured.
- Below 1200 px: one column, in the order results, chart, inputs; the density slider stays pinned at the
  bottom of the screen. Works from 390 px wide.
- Accessibility: WCAG 2.2 AA; every control keyboard operable; colour is never the only signal (bands have
  labels, warnings have icons, the hatching has a text label).
- All interface text sits in one strings file, ready for translation.

### 7.7 What it must not become

- A generic dashboard of cards and gauges.
- A form to fill in before anything is shown.
- A page that hides ranges or sources to look cleaner.
- A costume: no paper textures or fake map ornament.

### 7.8 Build process

The interface is built with the `impeccable` skill: the direction contract is recorded in a surface brief
before any code, the craft floor is read before UI edits, the finished pages go through its finish review,
and the resulting design system is written to `DESIGN.md`.

## 8. Deployment

One Vercel project, connected to the GitHub repo. `main` is production; every branch gets a preview.

**Primary configuration** (the one Vercel's documentation supports most directly):

- A root `pyproject.toml` declares the API's dependencies (`fastapi`, `numpy`, `pydantic`) and
  `[tool.vercel] entrypoint = "api.index:app"`. Vercel runs the FastAPI app as one function. Python
  functions "include all files from your project that are reachable at build time", with the project root
  as the working directory, so `apv_core/`, `apv_physics/`, `data/app/` and `data/weather/` are available.
- `api/index.py` puts `apv_core/src` and `apv_physics/src` on the import path, so no package install step
  depends on Vercel's handling of local path dependencies.
- `vercel.json` sets `buildCommand` to build the Vite app in `web/`, and excludes `research/`, `docs/`,
  tests and `web/node_modules` from the function.
- The built frontend is served from Vercel's CDN through FastAPI's `app.frontend("/", directory="web/dist")`,
  which Vercel documents for this case; API routes take priority.

**Fallbacks, in order**, if the primary configuration does not work as documented:

1. File-based: `api/index.py` as a Python function, `outputDirectory: web/dist`, and rewrites for `/api/*` and
   the single-page fallback.
2. Vercel Services (beta): a frontend service rooted at `web/` and a backend service at the repo root.

**The first build task is a deployment test.** A minimal API that runs one real sweep for one district,
plus a placeholder page, deployed to a preview. It must show:

| Check | Pass |
|---|---|
| The function imports `apv_physics` and `apv_core` and reads a weather pack | A real sweep returns over HTTPS |
| Bundle size | Under Vercel's 500 MB Python limit, with the 40 MB of packs |
| Response time, warm | 1.5 s or less at the 95th percentile over 20 requests (parent spec §7.1) |
| Response time, cold start | 8 s or less |
| Static page and `/api` routes on one domain | Both respond; a deep link to `/model/...` loads the app |

If a check fails, the configuration is changed (fallbacks above) before anything else is built. If none
passes, work stops and the owner decides.

The weather packs move from git-ignored to committed as part of this task.

## 9. Testing

Tests are written before the code they test.

| Part | Tests |
|---|---|
| `pipeline.appdata` | Unit tests for each rule in §5 (unit conversion, latest year, median fallback, state-name mapping, height interpolation); a check that the built files have 785 districts, 20 crops and the expected keys |
| `api` | FastAPI TestClient contract tests for every route: success shapes, default resolution, 404 and 422 with field names, cache reuse, the sweep against a direct `apv_core` call; a test that the OpenAPI schema matches the committed copy |
| `web` | Vitest: number formatting, URL encoding and decoding of scenarios, chart scales and the policy region, input validation, the tour's step and dismissal state. Playwright: search → Model shows a worked result with example crops → change a crop → move the density → copy link → reload gives the same result, at 1440 and 390 px, against a locally running API; the tour appears once and reopens from "How to read this". An axe accessibility check on all three pages |
| Deployment | The checks in §8, rerun as a script against any preview URL |

CI: one workflow each for `pipeline`, `api` and `web`, on changes to their folders. The web workflow also
checks that the generated TypeScript API types are up to date.

## 10. Success criteria for the slice

- The production URL serves the app; all 785 districts can be found and modelled.
- A sweep returns within the times in §8.
- Every pre-filled number on the Model page shows its source, year and whether it is a state figure, a
  national figure or an assumption.
- All tests and the accessibility check pass in CI.

## 11. Risks

| Risk | Effect | Handling |
|---|---|---|
| Vercel does not bundle sibling folders or serve the frontend as documented | No deployment | The deployment test is the first task; two fallbacks are listed |
| Cold start too slow (numpy import plus physics) | Misses the 8 s target | Measured in the first task; lazy imports and a smaller function bundle if needed |
| State-level 2021-22 economics mislead | Wrong farm income | Labelled on every value; editable; some state figures show costs above crop value (e.g. Maharashtra paddy), which the page reports as it is |
| Loan terms are placeholders | Wrong payback and IRR | Labelled as assumptions; research gap D21 |
| Draft crop parameters change | Results shift later | The data version is shown and returned with every result |
| 40 MB of binary files in git | Repo grows on each rebuild | Accepted by the owner; rebuilds are rare |

## 12. Edits to other documents

- `PRODUCT.md`, Operating Context: "Physics … is pre-computed" becomes "Physics is calculated live for the
  layout the user enters".
- Parent spec §15.3: add `GET /api/districts`; note the sweep response fields in §6 here.
- `.gitignore`: remove `data/weather/*.npz`.
- `SOURCE_pvgis_tmy.md`: the packs are committed and public.
