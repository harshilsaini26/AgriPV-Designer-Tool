# AgriPV Lab — Product Specification (PRD)

| | |
|---|---|
| **Product** | AgriPV Lab (working name), a district-level agrivoltaics knowledge tool for India |
| **Version** | 1.0, consolidated |
| **Date** | 2026-11-06 |
| **Owner** | Harshil (product); Claude (drafting) |
| **Status** | Draft for review |
| **Repo** | https://github.com/harshilsaini26/AgriPV-Designer-Tool (MIT licence) |
| **Supersedes** | `2026-11-06-agripv-district-modeller-design.md`; its technical design is folded into §11–§15 here |
| **Related** | [`PRODUCT.md`](../../../PRODUCT.md) · chosen visual direction sketch [`.impeccable/mocks/decision/model-pick.html`](../../../.impeccable/mocks/decision/model-pick.html) |

**How to read this:** §1–§9 are the product requirements. §10–§15 cover the experience, the model, data and system design that implement them. §16–§18 cover risks, open questions and phasing. Requirement IDs (e.g. `REQ-GCR-02`) are stable and referenced from tests and plans.

---

## 1. Problem statement

Agrivoltaics (APV) means growing crops and generating solar power on the same land. India is pushing it through PM-KUSUM, but the people who advise farmers have **no India-specific way to see roughly what APV would mean for a particular district**:
- how much crop yield would be lost to shade,
- how much energy income it would add,
- how that balance changes with panel density (GCR),
- and whether local conditions (groundwater stress, heat, slope, the main crops) help or hurt.

These advisers are FPOs, NGOs, EPC firms and consultants. Today they either use US-centric tools (NREL's ADAM: US tax, MACRS, US weather data, $/acre) or have no tool at all. Early conversations, including deals and policy discussions, therefore run on guesswork. The risk is that farmers sign leases or schemes that hurt farm output, or that good districts get overlooked.

Policy is also unsettled. Policymakers are proposing a **draft rule that yield must stay at or above 80% of the open-field level**, but no formal limit exists yet. People need a way to explore what different panel densities mean *now*, against the proposed rule.

## 2. Product positioning

**A knowledge tool, not a report generator.** AgriPV Lab gives **rough, honest estimates, shown as ranges, of what to expect after deploying APV in an Indian district**, built on stated assumptions with every number traced to its source. It isn't a DPR, a bankability assessment or a site design tool.

| | AgriPV Lab | NREL ADAM | Agrivoltaic experiment designer (saltysaguaro) |
|---|---|---|---|
| Geography | India, ~780 districts | US (NSRDB) | Any (weather upload) |
| Context layers | Agro-climate, soil, elevation, groundwater, crops, solar | None | None |
| Crop response | Seasonal (kharif/rabi/zaid), cited, evidence-graded | Single user-entered % | PAR/DLI only, no yield |
| Business models | PM-KUSUM A, land lease | US PPA + tax | None |
| Output style | Ranges + explainers | Point estimates | Light maps, reports |
| Licence / access | Open (MIT), free web app | Free web form, no API | Proprietary |

## 3. Goals

**User goals**
1. **G1 — Understand quickly.** A user who picks a district gets an indicative range for farm income, energy income and LER at their chosen GCR **within 3 minutes of landing** (median).
2. **G2 — See the trade-off.** Users can see where their chosen crops fall below the draft 80% yield-retention limit (the **allowed GCR range**) for any district, crop rotation and structure.
3. **G3 — Trust the source.** Every number on screen and in the Estimate Sheet can be traced to its data source, year, method and evidence grade, **within two clicks**.

**Project and portfolio goals**

4. **G4 — Defensible science.** The crop shade-response parameters reach the evidence and validation targets in §7.3 before public launch.
5. **G5 — Credible open artefact.** The repo, methodology pages and the cited data are good enough to share academically and to reuse under the MIT licence.

## 4. Non-goals (v1)

| Non-goal | Why it's out of scope |
|---|---|
| **Site-level or DPR-grade analysis** (custom geometry, substation distance, geotechnical conditions, parcel boundaries) | The data supports district resolution only. Claiming more would hurt credibility. |
| **Bank-grade finance as the headline** (DSCR covenants, debt sculpting, tax optimisation) | A knowledge tool gives indicative ranges. A small set of finance detail sits in an Advanced panel (P1), never the headline. |
| **Separate views per stakeholder group** | The same engine and outputs serve every group. Tailored views can come later if usage shows a need. |
| **PM-KUSUM Component C, captive use, C&I/open-access sale** | Different value streams. Deferred until A and lease are validated. |
| **User accounts, server-side storage, collaboration** | Not needed for a knowledge tool. URLs and browser storage are enough. |
| **Hindi or regional-language content** | Interface strings are ready for translation, but translation is a later phase. |
| **A composite "suitability score" with hidden weights** | Hard to defend. Transparent filters only (P1). |
| **Water balance** (water for panel cleaning, rainwater harvested from panels) | Parked; flagged only through the groundwater-context insights. |

## 5. Personas and stakeholders

| Persona | Context | What they want from AgriPV Lab |
|---|---|---|
| **P1 — FPO manager / CEO** | Runs a farmer producer organisation; is being approached by developers or considering KUSUM-A | "If our members put panels on their land, roughly what happens to their crop income, and is the lease we're offered reasonable?" |
| **P2 — NGO programme officer** | Supports farmer livelihoods and climate adaptation programmes | "Which crops and densities keep farming meaningful in this district, and what does that mean for groundwater?" |
| **P3 — EPC business-development engineer** | Looking for APV opportunities and early-stage proposals | "Roughly how many kWp per acre are realistic under the proposed yield rule, and what return range should we expect?" |
| **P4 — Consultant / analyst** | Prepares feasibility notes and policy briefs | "A consistent, cited comparison across districts and scenarios that I can quote with clear caveats." |
| **P5 — Researcher / student (secondary)** | Studies APV in India | "A transparent method and data trail I can check and build on." |

**Stakeholders who aren't users:**
- **Policymakers:** the source of the draft 80% limit. A possible future audience (parked).
- **Farmers:** reached through P1 and P2 and the Estimate Sheet.

## 6. User stories

Ordered by priority within each group. Each story maps to requirements in §8.

### 6.1 Core exploration (all personas)
- **US-01** As an FPO manager, I want to find my district by name or LGD code so that I can start without browsing a map. → REQ-DIS-01
- **US-02** As any user, I want to see my district's agro-climate, soil, terrain, groundwater, crops and solar resource in one place so that I understand the local context before modelling. → REQ-CTX-01..04
- **US-03** As an NGO officer, I want short, plain-language insights about the district (e.g. "most blocks over-exploited") so that I notice local risks without reading every number. → REQ-INS-01..02
- **US-04** As any user, I want to pick a business model, structure type and crop rotation from sensible defaults so that I get a result without knowing every parameter. → REQ-MOD-01..05
- **US-05** As any user, I want to move GCR freely from 0% to 50% and see results update immediately so that I build an intuition for the trade-off. → REQ-GCR-01..04
- **US-06** As any user, I want to see where my crops fall below the draft 80% yield-retention line so that I know which densities would likely be allowed under the proposed policy. → REQ-POL-01..04
- **US-07** As any user, I want results shown as ranges (low–central–high) so that I don't treat a rough estimate as exact. → REQ-RES-01..03
- **US-08** As any user, I want to see LER alongside income so that I understand whether combined land use beats single use. → REQ-LER-01..03
- **US-09** As an FPO manager, I want to see the farmer's income per acre before and after APV under KUSUM-A and under a lease so that I can compare the two models. → REQ-FIN-01..06
- **US-10** As an FPO manager, I want an indicative range for the maximum lease a developer could afford so that I have a reference point in conversations. → REQ-FIN-05
- **US-11** As any user, I want to download a one- or two-page Indicative Estimate Sheet so that I can share the result with colleagues or farmers. → REQ-OUT-01..04

### 6.2 Trust and learning
- **US-12** As a consultant, I want to see each number's source, year, method and evidence grade so that I can cite it responsibly. → REQ-PRV-01..04
- **US-13** As a newcomer to APV, I want short explainers on GCR, shade, seasons, LER and KUSUM so that I can understand the results without outside reading. → REQ-LRN-01..03
- **US-14** As a researcher, I want a methodology page with every equation and parameter table so that I can check or reproduce the estimates. → REQ-LRN-04

### 6.3 Comparison and sharing
- **US-15** As an analyst, I want to save up to three scenarios and compare them side by side so that I can contrast districts, structures or business models. → REQ-SCN-01..03
- **US-16** As any user, I want a shareable link that reproduces my scenario so that a colleague sees exactly what I saw. → REQ-SCN-04..05
- **US-17** As an EPC engineer, I want to filter districts by solar resource, groundwater stress and flat cropland so that I can shortlist where to look. → REQ-SCR-01..03 (P1)
- **US-18** As an EPC engineer, I want an Advanced panel with equity IRR, DSCR and LCOE ranges so that I can do a first check on viability. → REQ-ADV-01..02 (P1)

### 6.4 Edge cases and error states
- **US-19** As a user whose district lacks crop data, I want to be told clearly and to enter my own crop yields and prices so that I can still get an estimate. → REQ-CTX-04, REQ-MOD-04
- **US-20** As a user who picks a crop with weak or no shade-response evidence, I want a clear warning (or a manual-parameter option) so that I don't over-trust the result. → REQ-CRP-03..04
- **US-21** As a user whose inputs make the plant size fall outside the KUSUM-A range (0.5–2 MW), I want a warning so that I know the scheme may not apply. → REQ-FIN-04
- **US-22** As a user whose rotation can't meet the 80% limit at any GCR above 0, I want this stated plainly, with structures that might work suggested. → REQ-POL-04
- **US-23** As a user on a slow or failed connection, I want my inputs kept and a retry offered so that I don't lose my work. → REQ-ERR-01..03
- **US-24** As a user opening an old shared link after a data update, I want to be told the data has changed so that I understand why results differ. → REQ-SCN-05

## 7. Success metrics

Analytics must be privacy-friendly: no personal data, no cookies beyond the essentials (tool choice is an open question, Q-08). Targets are **hypotheses** for a knowledge tool with no paid acquisition. They're reviewed **1 month and 3 months after launch**.

### 7.1 Leading indicators

| Metric | Definition | Success | Stretch |
|---|---|---|---|
| Activation | % of sessions that select a district and reach a sweep result | ≥ 60% | ≥ 75% |
| Time to first result | Median time from landing to first result | ≤ 3 min | ≤ 90 s |
| GCR exploration | % of activated sessions that move the GCR slider at least twice | ≥ 50% | ≥ 70% |
| Trust engagement | % of activated sessions that open a source, explainer or "why this number" panel | ≥ 25% | ≥ 40% |
| Estimate Sheet exports | % of activated sessions that export an Estimate Sheet | ≥ 15% | ≥ 25% |
| Reliability | % of sweep requests that fail (5xx or timeout) | < 1% | < 0.2% |
| Performance | p95 sweep latency when the server is already running / on a cold start | ≤ 1.5 s / ≤ 8 s | ≤ 0.8 s / ≤ 5 s |

### 7.2 Lagging indicators

| Metric | Definition | Success (3 months) |
|---|---|---|
| Returning use | % of visitors who come back within 30 days | ≥ 20% |
| Breadth | Distinct districts modelled | ≥ 200 |
| External use | Documented uses (citations, FPO/NGO/EPC feedback, policy briefs) | ≥ 5 |
| Qualitative trust | Of interviewed users (n ≥ 8), the share who say they'd use the ranges in early-stage discussions | ≥ 6 of 8 |

### 7.3 Model quality targets (required before public launch)

| Target | Threshold |
|---|---|
| Crop coverage | Shade-response parameters for the **top 20 crops by national cropped area**, covering every season they're grown in |
| Evidence grade | Top 10 crops at **grade B or better**; the other 10 at **grade C or better** (grades defined in §13.3) |
| Yield validation | Across all published Indian APV / shade-trial data points collected, predicted relative yield is within **±15 percentage points** of observed for **≥ 80%** of points |
| Energy validation | pvlib annual energy within **±3%** of PySAM for 10 sample districts, and within **±7%** of Global Solar Atlas PV output |
| Data coverage | Every layer covers **≥ 95%** of districts; the crop layer covers **≥ 90%** |

## 8. Requirements

Priorities: **P0** = must ship in v1; **P1** = soon after launch; **P2** = future, but design so it stays possible.

### 8.1 District selection — `DIS`
**REQ-DIS-01 (P0) District search.** Search by district name (fuzzy, accepting transliteration variants) or LGD code, across all ~780 districts.
- [ ] Typing ≥ 2 characters shows up to 8 suggestions, each with district name, state and LGD code.
- [ ] Common spelling variants match (e.g. "Ahmednagar" / "Ahilyanagar"; "Gurgaon" / "Gurugram") using an alias table.
- [ ] Choosing a result opens that district's sheet in ≤ 1 s (static data).
- [ ] No match shows "No district found" plus a link to browse the map.

**REQ-DIS-02 (P0) Map selection.** An India map with district boundaries. Clicking a district selects it.
- [ ] Hover shows name and state; click opens the district sheet.
- [ ] Works with keyboard: the district list is reachable without the map.

**REQ-DIS-03 (P1) Recent districts.** The home page lists the last 5 districts or scenarios, stored in the browser.

### 8.2 District context — `CTX`
**REQ-CTX-01 (P0) Six layer panels.** The district sheet shows agro-climate, soil, elevation, groundwater and irrigation, crops (with economics), and solar, using the fields in §14.3.
- [ ] Every value shows units and, on hover or tap, source, data year and method.
- [ ] Values summarised from rasters are labelled "cropland-weighted".

**REQ-CTX-02 (P0) Map layers.** The district map can show slope, groundwater category, cropland mask and solar resource, switched on and off from a conventional-signs legend panel.

**REQ-CTX-03 (P0) Data-quality badges.** Any field flagged `missing`, `state_fallback`, `boundary_mapped` or `imputed` shows a badge with a one-line explanation.

**REQ-CTX-04 (P0) Missing data.** If a layer is missing for a district, its panel says what's missing and why. If crop data is missing, modelling stays available through manual crop entry (REQ-MOD-04).

### 8.3 Context insights — `INS`
**REQ-INS-01 (P0) Rule-based insights.** Show 2–5 plain-language insights per district, produced by rules in one YAML file that cites its reasoning.
- [ ] Each insight names the data that triggered it (e.g. "41% of blocks over-exploited, CGWB 2023").
- [ ] Rules can be changed without code changes; the file is validated in CI.

**REQ-INS-02 (P0) Starter rules.** At least: groundwater stress, heat stress (days above 40 °C), steep cropland share, a shade-sensitive main crop, a shade-tolerant main crop, high or low solar resource, and gaps in crop data.

### 8.4 Model inputs — `MOD`
**REQ-MOD-01 (P0) Business model.** Choose PM-KUSUM A (farmer/FPO owner) or land lease (developer-owned). Default: KUSUM-A.

**REQ-MOD-02 (P0) Structure preset.** Choose from:
- elevated fixed-tilt at 3 clearance heights,
- single-axis tracker at 2 heights,
- vertical bifacial (east–west),
- with a monofacial or bifacial module option where it applies.

Each preset shows a small diagram and its default farmable fraction (`a_farm`). Default: elevated fixed-tilt, middle height, bifacial.

**REQ-MOD-03 (P0) Crop rotation.** Choose a kharif crop, a rabi crop and an optional zaid crop. Defaults are the district's main crop by area in each season.
- [ ] Each crop shows its shade-tolerance group and evidence grade.
- [ ] Only crops grown in that season are listed; crops with no parameters are marked (REQ-CRP-03).

**REQ-MOD-04 (P0) Manual crop entry.** Users can override baseline yield, price and cultivation cost per crop. Overridden values are marked as "user-entered" everywhere, including the Estimate Sheet.

**REQ-MOD-05 (P0) Finance inputs.** Pre-filled with state defaults: CAPEX per kWp, O&M, KUSUM-A tariff, lease escalation, discount rate, analysis period (25 years). All editable, with "reset to defaults". Defaults show their source and date.

**REQ-MOD-06 (P0) Step-by-step inputs.** Inputs are grouped into ordered steps. Only the current step is expanded; finished steps collapse to one-line summaries that can be clicked to edit.

### 8.5 GCR exploration — `GCR`
**REQ-GCR-01 (P0) Free GCR range.** GCR can be set from **0.00 to 0.50 in steps of 0.05** (11 values), whatever the policy limit.
- [ ] **GCR 0.00 is the open-field baseline** (no structure, full yield, no energy). It's always the chart's starting point.

**REQ-GCR-02 (P0) Instant updates.** Moving the GCR slider updates every figure, chart and range without a new API call. One sweep per change of inputs returns all 11 values.
- [ ] Slider response ≤ 100 ms after the sweep has loaded.
- [ ] There is no "Run" button.

**REQ-GCR-03 (P0) Keyboard and touch.** Arrow keys move ±0.05; Home and End go to 0.00 and 0.50. The current value is announced to screen readers.

**REQ-GCR-04 (P0) Trade-off chart.** Across GCR the chart shows:
- farm share (green) and energy share (blue),
- the LER line (black),
- the selected GCR (survey-red marker),
- the draft policy line (REQ-POL-01),
- the low–high uncertainty band.

Season panels (kharif, rabi, zaid) **share one y-scale**.

### 8.6 Policy yield-retention limit — `POL`
**REQ-POL-01 (P0) Draft policy reference.** Show a **draft policy limit: yield ≥ 80% of open field** as a labelled reference line, "Proposed policy limit (draft)".
- [ ] Default 80%; editable in settings from 50–100% in steps of 5%. A non-default value is shown in the chart label and in the Estimate Sheet.

**REQ-POL-02 (P0) Not a block.** GCR values that break the limit stay selectable. They're shaded and marked "Outside proposed limit". Results still appear, with a warning.

**REQ-POL-03 (P0) Allowed GCR range.** The tool works out and shows the **highest GCR at which every crop in the rotation stays ≥ the limit**, using the central estimate and also the low–high range.
- [ ] Retention is measured **per acre of land** (`a_farm × Y_rel`) and **checked for each season**. This definition is provisional (Q-02, Q-03).

**REQ-POL-04 (P0) No allowed GCR.** If no GCR above 0 meets the limit, say: "No panel density in this range keeps [crop] at or above 80% yield". Then list the structure presets (if any) that would, based on the same district's physics.

### 8.7 Results as ranges — `RES`
**REQ-RES-01 (P0) Ranges first.** Headline results appear as **low–central–high**. Low and high come from the crop-response parameter range (and tariff and CAPEX ranges where they're defined), e.g. "₹38,000–52,000 / acre (central ₹46,000)".

**REQ-RES-02 (P0) Headline set at the selected GCR:**
- farm income per acre (with before/after),
- energy income per acre,
- total per acre,
- LER,
- farm yield retention %,
- kWp per acre,
- annual energy per acre,
- simple payback,
- project IRR.

**REQ-RES-03 (P0) Formatting.** All ₹ values use Indian grouping (lakh/crore). Units are always shown. Figures are tabular and rounded to sensible precision (no false precision; e.g. ₹ to the nearest ₹1,000 per acre).

### 8.8 LER — `LER`
**REQ-LER-01 (P0)** Compute LER as in §12.5, with an agri part (revenue-weighted across seasons) and an energy part (relative to a reference conventional PV plant).

**REQ-LER-02 (P0)** Show the reference PV assumption (ground-mounted fixed tilt, GCR 0.45, same district) next to LER, with a link to its explainer.

**REQ-LER-03 (P0)** Show per-season LER and the economic ratio (total income ÷ baseline farm income) as secondary figures.

### 8.9 Finance — `FIN`
**REQ-FIN-01 (P0) KUSUM-A cash flows.** A 25-year annual model of energy revenue at the state tariff, farm income, O&M and simple financing (debt share, interest rate, tenor). Outputs, as ranges: project IRR, NPV, simple payback, and net income per acre for the farmer/FPO.

**REQ-FIN-02 (P0) Lease cash flows.** The developer owns the plant. The farmer gets lease (per acre per year, with escalation) plus farm income on `a_farm`. Outputs: farmer income per acre before and after, and developer project IRR.

**REQ-FIN-03 (P0) Before and after.** For both models, show farmer income per acre before APV (baseline rotation) and after APV, side by side.

**REQ-FIN-04 (P0) KUSUM-A size check.** Warn when the plant size implied by land area × kWp per acre is outside 0.5–2 MW. A land-area input defaults to the size that gives 2 MW.

**REQ-FIN-05 (P0) Maximum affordable lease.** Show the maximum lease a developer could pay at a target project IRR (default 12%, editable) as a range, using the closed form in §12.6.
- [ ] Negative results show "Not viable at target IRR".

**REQ-FIN-06 (P0) Edge cases.** IRR with no sign change in the cash flows returns "IRR undefined" with the reason, never NaN or a crash.

### 8.10 Advanced finance — `ADV` (P1)
**REQ-ADV-01 (P1)** A collapsed Advanced panel with equity IRR, minimum and average DSCR, LCOE (all as ranges), and loan structure inputs.

**REQ-ADV-02 (P1)** Tax inputs: tax rate and WDV depreciation, defaults to be checked against current Income Tax rules. The panel is labelled "indicative only, not for financing decisions".

### 8.11 Outputs — `OUT`
**REQ-OUT-01 (P0) Indicative Estimate Sheet (PDF).** A 1–2 page print-ready sheet with:
- a title block: district, data edition, date, scenario link and QR code,
- context summary and insights,
- inputs and assumptions,
- the trade-off chart with the policy line and the selected GCR,
- headline ranges,
- warnings,
- sources legend,
- and the fixed note: *"Indicative estimate for exploration. Not a detailed project report, financial advice or site assessment."*

**REQ-OUT-02 (P0)** The Estimate Sheet is produced by a print stylesheet in the browser (no server PDF rendering). It looks correct on A4 in Chrome, Edge and Firefox.

**REQ-OUT-03 (P0)** User-entered or overridden values and a non-default policy limit are visibly marked on the sheet.

**REQ-OUT-04 (P1) Excel export.** A workbook with inputs, assumptions, per-GCR results and the yearly cash flows at the selected GCR, generated by the API (openpyxl).

### 8.12 Scenarios — `SCN`
**REQ-SCN-01 (P0) Save.** Save the current scenario (all inputs + selected GCR) in the browser, with an editable name.

**REQ-SCN-02 (P0) Compare.** Compare up to 3 saved scenarios side by side: headline ranges, allowed GCR range, and small trade-off charts on a **shared scale**.

**REQ-SCN-03 (P0) Empty state.** The compare view with fewer than 2 scenarios explains how to add one.

**REQ-SCN-04 (P0) Shareable URL.** Every scenario has a URL that encodes all its inputs, the selected GCR, the policy limit and `data_version`. Opening it reproduces the same results on the same data version.

**REQ-SCN-05 (P0) Data version change.** If a URL's `data_version` doesn't match the current one, show: "Built on data vX; now vY. Results may differ."

### 8.13 District screening — `SCR` (P1)
**REQ-SCR-01 (P1)** A "Find districts" tab with filters: GHI/PV output range, % of groundwater units over-exploited or critical, % of cropland below 5° slope, main-crop shade tolerance, agro-climatic zone.

**REQ-SCR-02 (P1)** Matching districts are highlighted on the map and listed in a sortable table.

**REQ-SCR-03 (P1)** No combined score: the filters are fully visible and explained.

### 8.14 Learning layer — `LRN`
**REQ-LRN-01 (P0) Explainers.** Short explainers (≤ 150 words + one diagram each) on: GCR, shade and light, crop seasons, LER, the draft policy limit, PM-KUSUM A, land lease, groundwater categories, reading ranges.

**REQ-LRN-02 (P0) "Why this number".** Every headline figure has a panel that shows the steps of its calculation and the main inputs.

**REQ-LRN-03 (P1) First-visit tour.** A dismissible 3-step guide on the first visit (search → model → read the trade-off).

**REQ-LRN-04 (P0) Method and sources pages.** Every equation, parameter table (with evidence grades and citations), data source with licence, and known limitation.

### 8.15 Provenance — `PRV`
**REQ-PRV-01 (P0)** Every data field has source, data year, method and licence in `sources.json`, reachable from the UI within two clicks.

**REQ-PRV-02 (P0)** Every crop parameter shows its evidence grade and citations.

**REQ-PRV-03 (P0)** The data version and build date appear in the footer, the Estimate Sheet and the API responses.

**REQ-PRV-04 (P0)** All warnings returned by the API are shown in the UI and on the Estimate Sheet.

### 8.16 Crop parameter library — `CRP`
**REQ-CRP-01 (P0)** Each crop record holds: name (English, with Hindi to come), seasons, shade-tolerance group, `(L_t, k)` at low, central and high, evidence grade, citations, notes, and the climate and region of the source studies.

**REQ-CRP-02 (P0)** Coverage and grade targets as in §7.3.

**REQ-CRP-03 (P0)** Crops below grade C, or with no parameters, can't be chosen by default. They show "Insufficient evidence". A user can still enter their own parameters in Advanced, which are labelled user-entered.

**REQ-CRP-04 (P0)** Any rotation that uses a grade C or D crop shows a warning in results and on the Estimate Sheet.

**REQ-CRP-05 (P1) Heat-relief uplift.** An optional, capped uplift for districts with many days above 40 °C. **Off by default**, cited, and clearly labelled when on.

### 8.17 Data pipeline — `PIP`
**REQ-PIP-01 (P0)** Build all layers for all LGD districts. Raster statistics are cropland-weighted (§14.2).

**REQ-PIP-02 (P0)** Validation on every source: structure, row counts, plausible ranges, district coverage thresholds (§7.3). The build fails if a threshold isn't met.

**REQ-PIP-03 (P0)** Build outputs (§14.4) are versioned with a manifest and checksums. Builds can be safely re-run. Raw downloads are cached locally and not committed.

**REQ-PIP-04 (P0)** Physics is pre-computed for every district × configuration × GCR (§12.1) and checked against PySAM and Global Solar Atlas (§7.3).

**REQ-PIP-05 (P0)** Mapping between old and new district boundaries, with the `boundary_mapped` flag.

### 8.18 API — `API`
**REQ-API-01 (P0)** Endpoints and contract as in §15.3. Pydantic validation, with field-level 422 errors.

**REQ-API-02 (P0)** The OpenAPI schema generates the frontend's TypeScript types; CI fails if they drift apart.

**REQ-API-03 (P0)** `warnings[]` and `data_version` appear in every model response.

### 8.19 Error handling — `ERR`
**REQ-ERR-01 (P0)** While recalculating, the previous result stays visible but dimmed. On a slow response (cold start), progress shows inside the chart frame.

**REQ-ERR-02 (P0)** On a network error or timeout (> 15 s), show the error with a retry button. All inputs are kept.

**REQ-ERR-03 (P0)** Validation errors appear next to the input that caused them, in plain language, saying what's wrong and how to fix it.

**REQ-ERR-04 (P0)** Unknown district or configuration → a clear 404 or 422 and a UI message; never a 500 with a stack trace.

### 8.20 Non-functional — `NFR`
**REQ-NFR-01 (P0) Performance.** First contentful paint ≤ 2.0 s on a mid-range laptop over 4G. District sheet ≤ 1 s after selection. Sweep latency as in §7.1.

**REQ-NFR-02 (P0) Accessibility.** WCAG 2.2 AA:
- contrast ≥ 4.5:1 for body text,
- colour never the only signal (series also differ by line style or pattern),
- full keyboard operation,
- a data table version of every chart,
- visible focus.

**REQ-NFR-03 (P0) Screen sizes.**
- Desktop-first, 1280–1600 px.
- Tablet: margin panels stack below the sheet.
- Phone (≥ 360 px): read-only results and Estimate Sheet, with no horizontal scrolling.

**REQ-NFR-04 (P0) Translation-ready.** All interface text lives in translation files. Number formatting goes through one formatting utility that supports Indian grouping.

**REQ-NFR-05 (P0) Browsers.** The latest 2 versions of Chrome, Edge, Firefox and Safari.

**REQ-NFR-06 (P0) Privacy.** No personal data collected. Analytics are aggregate and cookie-free (Q-08).

**REQ-NFR-07 (P0) Licensing.** Code under MIT. Data attributions follow each source's licence on the Sources page and the Estimate Sheet.

**REQ-NFR-08 (P0) Hosting.** Runs within Vercel's limits (function bundle size, duration, memory). Moving to Pro before any commercial use (Q-09).

### 8.21 Future considerations — P2 (design so these stay possible)
- **P2-01** PM-KUSUM C and C&I/open-access models: the finance module accepts pluggable cash-flow models.
- **P2-02** Hindi and regional languages: the translation layer and Devanagari-capable fonts are in place from v1.
- **P2-03** Water balance (cleaning water, rainwater harvesting): add district water fields to the pipeline schema.
- **P2-04** Policymaker view: limit scenarios across many districts. Data model supports batch sweeps.
- **P2-05** User-supplied site data (custom TMY, geometry): the API accepts optional overrides.
- **P2-06** A sub-district (block) level where data allows: the pipeline keys on generic admin units, not only districts.

## 9. Assumptions

| # | Assumption | If wrong |
|---|---|---|
| A-1 | District-level data is enough for indicative estimates | Users ask for site precision → keep it out of scope, point to detailed design tools |
| A-2 | Published shade-response studies can support grade-B parameters for the top 10 crops | Lower evidence grades and wider ranges; more crops marked "insufficient evidence" |
| A-3 | The draft 80% limit applies per acre of land, checked per season | Change the retention definition (one function); the allowed GCR range changes |
| A-4 | State KUSUM-A tariffs can be found from public orders | Use national benchmark tariffs with a `state_fallback` flag |
| A-5 | A one-call sweep fits Vercel function limits | Move physics into per-district fetched files; still no pvlib at runtime |

---

## 10. Experience design

### 10.1 Visual direction: Toposheet (chosen)
The look is based on Survey of India topographic sheets. It's a working tool (Operate mode): familiar patterns and standard controls come first, and the visual style shows only through type, palette, density and one signature element.
- **Type:** Barlow Condensed for sheet titles and map labels; Barlow for the interface; tabular figures throughout.
- **Palette (each colour has a job):**
  - off-white sheet ground (not cream), black ink
  - contour brown: slope and terrain
  - water blue: groundwater and the **energy** series
  - vegetation green: cropland and the **farm** series
  - black: **LER**
  - survey red: **only** the selected GCR and the allowed-range limit marker
  - ochre plus an icon: warnings
  - grey hatching: values outside the draft policy limit
- **Density:** fine hairlines, small labels, compact panels.
- **Signature element:**
  - Maps and charts sit inside **sheet margins with grid-reference ticks**.
  - The selected GCR is marked as a **survey reference point** (red triangle), on the chart, in the results and on the Estimate Sheet.
  - The layer legend is a **conventional-signs panel**.
  - The Estimate Sheet has a **toposheet-style title block**.

### 10.2 Information architecture
`Home` · `District` (context sheet) · `Model` · `Compare` · `Estimate Sheet` · `Learn` (explainers) · `Method & Sources` · `Find districts` (P1)

### 10.3 Primary flow (searching for a district comes first)
1. **Home:** large search over an India sheet, recent scenarios, link to Learn.
2. **District sheet:**
   - the district map leads, inside graticule margins,
   - the conventional-signs legend switches layers,
   - six layer panels in the sheet margin, with badges,
   - insights,
   - primary action: **Model this district**.
3. **Model:** the map shrinks to a **locator inset** and the trade-off chart takes the sheet body.
   - **Left:** input steps.
   - **Centre:** the chart with the GCR slider (0–0.50), the draft policy line and the uncertainty band; season panels below on a shared scale.
   - **Right:** headline ranges for the selected GCR, the allowed GCR range, warnings, and the Estimate Sheet and Save actions.
   - **Below the visible screen:** before/after per acre, cash-flow summary, data table, Advanced (P1).
4. **Compare:** up to 3 scenarios.
5. **Estimate Sheet:** print preview → PDF.

### 10.4 Key states
- **Loading:** dimmed previous result; progress inside the chart frame on a cold start.
- **Errors:** retry; inputs kept.
- **Missing data:** panel explains; manual entry offered.
- **Insufficient crop evidence.**
- **No allowed GCR.**
- **KUSUM-A size out of range.**
- **Empty compare.**
- **Data version mismatch.**
- **First visit:** tour (P1).
- **Long district names** (e.g. "Sri Potti Sriramulu Nellore") wrap neatly in headers and on the sheet.

---

## 11. System architecture

- **`pipeline/`** (offline Python): fetch → clean → aggregate to districts → simulate physics → validate → build artefacts.
- **`apv_core/`** (Python package): crop response, LER, finance, sweep, ranges. Pure functions, no I/O, fully unit-tested.
- **`api/`**: FastAPI on Vercel's Python runtime. Imports `apv_core`; bundles `physics.parquet`, `crops.json` and `finance_defaults.json`.
- **`web/`**: Vite + React + TypeScript; MapLibre GL; charts; print stylesheet for the Estimate Sheet.
- **`data/`**: versioned build outputs; static context and boundaries copied to `web/public/data/` for the CDN.
- **`docs/`**: specs, methodology source, sources register.

**Core decision: physics offline, economics live.** pvlib runs only in the pipeline. The API does numpy-only calculations on pre-computed lookups, so the function stays small and quick to start on Vercel. *Trade-off:* structure presets only, no free geometry.

**One sweep per change of inputs.** `POST /api/sweep` returns all 11 GCR values at low, central and high. The slider reads results already loaded in the browser.

## 12. Model specification

### 12.1 Physics (offline, pvlib)
- **Configuration grid** (with GCR ∈ {0.05 … 0.50}, 10 values; GCR 0.00 is the analytical baseline):
  - elevated fixed-tilt: 3 clearance heights × {mono, bifacial} = 60
  - single-axis tracker: 2 hub heights × {mono, bifacial} = 40
  - vertical bifacial east–west: 10
  - total **110 configurations per district**
- **Energy:** pvlib simulation on the district TMY, with standard losses and bifacial gain where it applies. Stored as monthly AC energy per kWp, `E[m]`.
- **Ground light:** a 2-D view-factor model across the row pitch (infinite-sheds geometry). It covers direct-beam shadow plus diffuse light from the visible sky, on a ground line across the row, averaged over the cultivable band. Stored as the monthly ground light fraction relative to open field, `L[m]`. PAR is taken as a fixed fraction of shortwave.
- **Reference PV for LER:** ground-mounted fixed tilt at GCR 0.45 in the same district. Stored as `E_ref` per acre.
- **GCR definition for vertical bifacial:** module height ÷ row pitch (documented in Method).

### 12.2 Land use
- `kWp_per_acre = GCR × 4046.86 m² × η_module × 1 kW/m²`
- `a_farm`: farmable fraction per structure preset (default per preset, editable in Advanced). At GCR 0, `a_farm = 1`.

### 12.3 Crop shade response
- `L_s` = mean of `L[m]` over the months of season s (kharif June–October, rabi November–March, zaid March–June).
- `Y_rel = 1` if `L_s ≥ L_t`, else `max(0, 1 − k × (L_t − L_s))`.
- Evaluated at the low, central and high `(L_t, k)`.
- Optional heat-relief uplift (P1, off by default): `Y_rel ← min(Y_rel × (1 + u), 1 + u_cap)`, where `u` depends on days above 40 °C.

### 12.4 Yield retention and farm income
- `retention_s = a_farm × Y_rel,s`. Policy check: `retention_s ≥ limit` for every season s (provisional, Q-02/Q-03).
- `I_farm = Σ_s [ Y_base,s × Y_rel,s × a_farm × price_s − cost_s × a_farm × (1 + p_apv) ]`
- Baseline: `Y_rel = 1`, `a_farm = 1`, `p_apv = 0`.

### 12.5 LER and economic ratio
- `LER = agri_term + energy_term`
  - `agri_term = Σ_s w_s × a_farm × Y_rel,s`, where `w_s` = season's share of baseline crop revenue
  - `energy_term = (kWp_per_acre × Σ_m E[m]) ÷ E_ref_per_acre`
- `economic_ratio = (I_farm + I_energy) ÷ I_farm,baseline`

### 12.6 Finance (25 years, annual)
- **KUSUM-A:** cash flow in year t = `tariff × energy_t + I_farm,t − O&M_t − debt service_t`, with degradation and escalation. Outputs: project IRR, NPV, simple payback (P0); equity IRR, DSCR, LCOE (P1).
- **Lease:**
  - developer cash flow = `tariff × energy_t − O&M_t − lease_t`
  - farmer income = `lease_t + I_farm,t`
  - `lease_max = NPV_dev,no-lease(r_target) ÷ AF`, where `AF = Σ_t (1+g)^(t−1) / (1+r_target)^t` (escalating annuity factor)
  - cross-checked numerically in tests
- **Ranges:** low, central and high combine the crop-response range with the editable tariff and CAPEX ranges (defaults ±10%). The low case pairs low yield with low tariff and high CAPEX; the high case the reverse.

### 12.7 Allowed GCR range and selection
- `allowed_GCR = max{ GCR : retention_s(GCR) ≥ limit for all s }`, computed for the central case and as a low–high range.
- Selected GCR: chosen by the user (default = central `allowed_GCR`, or 0.25 if none exists).

## 13. Crop evidence framework

### 13.1 Parameter record (in `crops.json`)
`id, name_en, name_hi (later), seasons[], tolerance_group, L_t{low,central,high}, k{low,central,high}, evidence_grade, citations[], study_regions[], study_climates[], notes, last_reviewed`

### 13.2 Research process
1. Search the literature: Indian APV pilots and shade-net/agroforestry shading trials, then international APV studies.
2. Extract relative yield against shade or light fraction, then fit `(L_t, k)` per study.
3. Combine across studies: central = weighted median; low and high = spread across studies (or ± a default when there's only one study).
4. Grade the evidence (§13.3), record the citations and peer-review the record.

### 13.3 Evidence grades

| Grade | Meaning |
|---|---|
| **A** | ≥ 2 Indian field studies (APV or controlled shade) in comparable climates |
| **B** | 1 Indian field study, **or** ≥ 2 international studies in comparable climates |
| **C** | 1 international study, or a well-supported extension from a closely related crop |
| **D** | Expert assumption only: can't be chosen by default (REQ-CRP-03) |

### 13.4 Validation
A held-out set of observed (light fraction, relative yield) points from Indian studies. Target: ≥ 80% of points within ±15 percentage points (§7.3). Results are published on the Method page.

## 14. Data specification

### 14.1 District list and boundaries
A canonical LGD-keyed list (~780 districts) with simplified recent boundaries, plus an old-to-new district lookup table for sources on older boundaries (`boundary_mapped`).

### 14.2 Cropland weighting
Before averaging rasters over a district, mask them to cropland using ESA WorldCover. Statistics describe cropland in the district.

### 14.3 Layers (candidate sources; licences confirmed in Phase 0)

| Layer | Candidate source | Stored fields |
|---|---|---|
| Agro-climate | Planning Commission 15 zones; NBSS&LUP agro-ecological sub-regions; IMD gridded rainfall (0.25°) & temperature | zone; sub-region; kharif, rabi and annual rainfall normals; days above 40 °C; aridity index |
| Soil | ISRIC SoilGrids 250 m; NBSS&LUP | dominant texture; mean pH, organic carbon, depth to bedrock |
| Elevation | Copernicus GLO-30 | mean, P10, P90 elevation; mean slope; % of cropland below 5° |
| Groundwater / irrigation | CGWB Dynamic Ground Water Resources (latest); DES land-use; Minor Irrigation Census | stage of extraction %; share of units over-exploited, critical, semi-critical or safe; % net irrigated area; irrigation mix |
| Crops | DES area/production/yield (5-year average); ICRISAT district database fallback | top crops per season with area and yield |
| Crop economics | CACP cost of cultivation (state); MSP; Agmarknet | price per quintal; cost per acre (state fallback flagged) |
| Solar | PVGIS TMY at the cropland centroid; Global Solar Atlas | annual and monthly GHI; PV output per kWp; hourly TMY (offline only) |

### 14.4 Build outputs
- `districts.parquet` / `.json`
- `boundaries.geojson` (or `.pmtiles`)
- `physics.parquet` (district × config × GCR × month: `E`, `L`; plus `E_ref`)
- `crops.json`
- `finance_defaults.json` (state tariffs, CAPEX, O&M with source and date)
- `insight_rules.yaml`
- `sources.json`
- `manifest.json` (version, date, checksums, coverage)

### 14.5 Data-quality flags
`missing`, `state_fallback`, `boundary_mapped`, `imputed`, `user_entered` (the last is UI-only).

## 15. Technical specification

### 15.1 Stack
- **Frontend:** Vite, React, TypeScript, MapLibre GL, a charting library (picked in the web plan), and Barlow / Barlow Condensed fonts served from the project.
- **API:** FastAPI on Vercel's Python runtime; numpy and pydantic.
- **Pipeline:** pvlib, PySAM (validation only), rasterio and geopandas.
- **Tooling:** pytest, Hypothesis, Vitest, Playwright, GitHub Actions.

### 15.2 Hosting
Vercel (Hobby now; **Pro before any commercial use**). Static frontend and data on the CDN; one Python function for the API.

### 15.3 API contract

| Method & path | Request | Response |
|---|---|---|
| `GET /api/meta` | — | data_version, build date, coverage, configurations, crops (id, name, seasons, grade), policy-limit default |
| `GET /api/district/{lgd}` | — | context row, flags, insights, default rotation, finance defaults |
| `POST /api/sweep` | district, business model, configuration, rotation (+ overrides), finance inputs, policy limit | `gcr[]` (11) × {low, central, high} for every headline metric; allowed GCR range; per-season retention; cash-flow summary at the default GCR; `warnings[]`; `data_version` |
| `POST /api/export/xlsx` (P1) | same as sweep + selected GCR | xlsx file |

Errors: 422 with field-level details; 404 for an unknown district or configuration.

### 15.4 Testing strategy
- **`apv_core`:**
  - finance against hand-worked reference cases
  - closed-form maximum lease against a numerical search
  - LER arithmetic
  - retention and allowed-range logic
  - crop-curve properties (never above 1, never rising as light falls)
- **Property tests (Hypothesis):** a higher tariff never lowers IRR; a higher GCR never raises retention; GCR 0 equals the baseline exactly.
- **Pipeline:** structure, range and coverage checks; snapshot tests for sample districts; physics checked against PySAM and Global Solar Atlas.
- **Crop evidence:** schema validation of `crops.json`; validation-set error check (§13.4) in CI.
- **API:** TestClient contract tests; OpenAPI → TypeScript type check in CI.
- **Web:**
  - Vitest for formatting (lakh/crore), state handling and URL encoding of scenarios
  - Playwright end-to-end: search → model → move GCR → Estimate Sheet, at 1440 and 390 px
  - an accessibility check (axe) on the main pages
- **CI:** all of the above on every pull request; pipeline validation when pipeline code changes.

---

## 16. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Weak crop evidence for major crops | High | High | Evidence grades, wider ranges, "insufficient evidence" state, research phase before launch |
| Users treat ranges as exact | Medium | High | Ranges first, the fixed note on every sheet, "why this number" panels |
| The final policy limit or its definition differs from the draft | Medium | Medium | Editable limit; retention defined in one function (A-3) |
| Crop economics data is noisy or state-level | High | Medium | Flags, editable values, rounding without false precision |
| Data licence restrictions (IMD, Agmarknet) | Medium | Medium | Check in Phase 0; swap to open alternatives (e.g. ERA5/NASA POWER for climate) |
| Vercel function limits or cold starts | Low | Medium | Numpy-only API; fallback in A-5 |
| District boundary changes | Medium | Low | LGD keys, lookup table, `boundary_mapped` flag |

## 17. Open questions

| ID | Question | Owner | Blocking? |
|---|---|---|---|
| Q-01 | What will the final yield-retention limit be, and when will it be decided? | Stakeholder (policymakers) | No — editable, default 80% |
| Q-02 | Is retention measured per acre of land (`a_farm × Y_rel`) or per cropped area (`Y_rel`)? | Stakeholder + data | **Yes for `apv_core`** — default to per acre of land until answered |
| Q-03 | Does the limit apply to each season's crop separately, or to the whole year's rotation? | Stakeholder | **Yes for `apv_core`** — default to per season |
| Q-04 | Which crops make up the top 20 for parameter research? Confirm from DES national area data. **Partly answered (2026-11-07):** `research/06_crops/area_production_yield/top20_national.csv`. Ranks 1–15 are firm (rice, wheat, soybean, cotton, maize, gram, mustard, bajra, sugarcane, moong, groundnut, tur, jowar, urad, guar). Ranks 16–20 (lentil, sesame, ragi, castor, barley) compete with potato, onion, tomato, mango, banana and coconut, whose national areas still need DA&FW horticulture estimates | Data | Yes for research phase |
| Q-05 | Do IMD gridded data and Agmarknet licences allow public, attributed use in an open-source app? | Legal / data | Yes for pipeline |
| Q-06 | Where are the official state-wise KUSUM-A tariffs published? | Data | No — national fallback |
| Q-07 | Product name and domain | Stakeholder | No |
| Q-08 | Which privacy-friendly analytics tool (e.g. Vercel Web Analytics, Plausible, self-hosted Umami)? | Engineering | No |
| Q-09 | Will any commercial user use it at launch (meaning Vercel Pro is required)? | Stakeholder | No |
| Q-10 | Default tariff and CAPEX range for the low/high cases (±10% proposed) | Data | No |
| Q-11 | Should the Estimate Sheet include a Hindi summary in v1? | Stakeholder | No |

## 18. Timeline and phasing

There are no hard external deadlines. Work is delivered in phases, and **each sub-project gets its own implementation plan**:

| Phase | Scope | Exit criteria |
|---|---|---|
| **0 — Research and data access** (runs alongside phase 1) | Crop parameter literature review (§13), licence checks (Q-05), KUSUM tariff sourcing (Q-06), answers to Q-02 and Q-03 | `crops.json` meets the §7.3 targets (draft); licences cleared |
| **1 — `apv_core`** | Crop response, retention and allowed range, LER, KUSUM-A and lease finance, ranges, sweep; tested on synthetic fixtures | All `apv_core` tests passing; reference cases match |
| **2 — `pipeline`** | District list, six layers, cropland weighting, physics, validation, build outputs | Coverage and physics validation targets met |
| **3 — `api`** | FastAPI on Vercel, bundled data files, contract, OpenAPI types | Contract tests passing; latency targets on a preview deployment |
| **4 — `web`** | Toposheet UI: home, district sheet, model, compare, Estimate Sheet, Learn, Method | End-to-end and accessibility checks passing; P0 acceptance criteria met |
| **5 — Validation and beta** | 8+ user interviews (FPO, NGO, EPC, consultant); crop validation published | §7.3 met; qualitative trust ≥ 6/8 |
| **Launch** | Public release; analytics on | — |
| **Post-launch (P1)** | Advanced finance, Excel export, district screening, first-visit tour, heat-relief uplift | — |

**Dependencies:** Phases 1 and 2 can run in parallel once the data formats (§12.1, §14.4) are fixed. Phase 3 needs both. Phase 4 can begin against a mocked API from the OpenAPI schema. Phase 5 needs the outputs of Phase 0.

## 19. Glossary

| Term | Meaning |
|---|---|
| **APV / Agri-PV** | Agrivoltaics: crops and solar PV on the same land |
| **GCR** | Ground coverage ratio: module area ÷ ground area (0 = no panels) |
| **LER** | Land equivalent ratio: agri yield share + energy yield share; > 1 means combined use beats separate use |
| **Yield retention** | APV crop yield per acre ÷ open-field yield per acre |
| **PM-KUSUM A** | Indian scheme component for farmer- or FPO-owned grid-connected solar plants of 0.5–2 MW selling to the DISCOM |
| **FPO** | Farmer Producer Organisation |
| **EPC** | Engineering, procurement and construction firm |
| **DPR** | Detailed Project Report |
| **LGD** | Local Government Directory (India's official administrative codes) |
| **Kharif / Rabi / Zaid** | Monsoon / winter / summer cropping seasons |
| **TMY** | Typical meteorological year (hourly weather file) |
| **PAR** | Photosynthetically active radiation |
| **DSCR** | Debt service coverage ratio |
| **WDV** | Written-down-value depreciation |
| **CGWB** | Central Ground Water Board |
