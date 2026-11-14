# Live physics engine — design

| | |
|---|---|
| **Date** | 2026-11-14 |
| **Status** | Draft for owner review |
| **Parent spec** | [`2026-11-06-agripv-lab-product-spec.md`](2026-11-06-agripv-lab-product-spec.md) (§11, §12.1, §14.4, §15) |
| **Replaces** | The "physics offline" decision in the parent spec §11 and the precomputed `physics.parquet` |

## 1. What this is

A user picks a district and a panel layout. The app must return, for 10 panel densities (GCR 0.05–0.50):

- the energy the panels produce each month, per kWp;
- the share of open-field light that reaches the crop each month;
- how even that light is across the field.

The owner decided (2026-11-14) that these are **calculated live**, for whatever layout the user enters. They
are not precomputed for a fixed list of layouts. This document designs the two parts that make that possible:

1. **`apv_physics`**: a small numpy-only Python package that does the calculation.
2. **Weather packs**: one small file per district, built offline, holding the hourly weather and sun positions
   the calculation needs.

## 2. Decisions already made

| Decision | Choice | Why |
|---|---|---|
| When physics runs | Live, per request | Users can edit the layout freely; no table of precomputed layouts to store |
| Engine | Our own, numpy only | pvlib and its dependencies are 236 MB installed (measured), against a 250 MB limit on the planned Vercel function, and add about 2 s to a cold start. numpy alone is 43 MB |
| pvlib and PySAM | Used offline and in tests only | They build the weather packs and prove the engine is right |
| Crop yield and height | Yield uses average light; evenness is reported beside it | Crop trials measured average light. In this model, height changes evenness, not the average (§5.4) |
| Editable settings | Tilt and facing direction, panel height, row width, module specs | Owner choice. Presets remain as starting points |

Storage note: live calculation stores **more** than precomputing would. The precomputed table would have been a
few MB; the weather packs are about 30–50 MB in total. The gain is the freedom to edit layouts.

## 3. Scope

**In scope**

- The `apv_physics` package: inputs, calculation, outputs, limits and tests.
- The weather-pack format and the offline script that builds the packs.
- Validation against pvlib, PySAM and the Global Solar Atlas.
- The edits this forces in the parent spec (§10).

**Out of scope** (each gets its own design later)

- The API: endpoints, caching, and where the weather packs are hosted.
- The web screens for editing a layout.
- Default costs for non-preset heights (finance defaults).
- The rest of the pipeline: district context, crops, finance defaults, manifest.

## 4. Architecture

```
offline                                   live (inside the API function)
-------                                   ------------------------------
calibrated hourly weather  ──┐
(785 districts, local)       ├─► pipeline.weather ─► weather pack ─► apv_physics.simulate(weather, layout)
pvlib sun positions        ──┘   (one .npz per district)                    │
                                                                            ▼
                                                              PhysicsTable ─► apv_core.run_sweep(...)
```

- **`apv_physics/`** sits beside `apv_core/` at the repo root. It depends on `numpy` and on `apv_core` (for
  `GCR_GRID`, `ACRE_M2` and `PhysicsTable`). It does no network access. Its only file access is reading a
  weather pack that the caller hands it.
- **`pipeline/`** is a new offline package. Its first component, `pipeline.weather`, builds the weather packs.
  It may use pvlib, pandas and anything else, because it never runs on the server.
- **`apv_core`** does not change. The engine returns the `PhysicsTable` that `run_sweep` already takes.

## 5. The engine (`apv_physics`)

### 5.1 Inputs

**`Weather`** (frozen dataclass; arrays share one length `n`, daylight hours only)

| Field | Unit | Meaning |
|---|---|---|
| `month` | 1–12 | Calendar month of each hour |
| `ghi`, `dni`, `dhi` | W/m² | Calibrated global horizontal, direct normal and diffuse horizontal irradiance |
| `temp_air` | °C | Air temperature at 2 m |
| `wind_speed` | m/s | Wind speed at 10 m |
| `zenith`, `azimuth` | degrees | Apparent sun zenith and azimuth (0 = north, clockwise) at the hour's time stamp |
| `dni_extra` | W/m² | Extraterrestrial normal irradiance |
| `latitude`, `longitude`, `elevation_m` | | The district point |
| `optimum_tilt_deg` | degrees | Global Solar Atlas optimum tilt at the point |

**`Module`**

| Field | Limits | Preset values (bifacial / monofacial) |
|---|---|---|
| `efficiency` | 0.15–0.25 | 0.225 / 0.210 |
| `bifaciality` | 0–0.95 | 0.80 / 0 |
| `temp_coeff_per_c` | −0.005 to −0.002 | −0.0030 / −0.0035 |

**`Layout`**

| Field | Applies to | Limits | Meaning |
|---|---|---|---|
| `kind` | all | `fixed`, `tracker`, `vertical` | Structure type |
| `tilt_deg` | fixed | 0–40 | Panel tilt from horizontal. Vertical is always 90 |
| `azimuth_deg` | fixed, vertical | 90–270 | Direction the front faces (180 = south). Vertical default 90 (faces east and west) |
| `max_angle_deg` | tracker | 30–60 | Turning limit either side of flat. Axis runs north–south; backtracking is always on |
| `height_m` | all | 0.5–6.0 | Fixed and vertical: lower panel edge above the ground. Tracker: axis height |
| `collector_width_m` | all | 0.5–10.0 | Panel surface width across the row (for vertical, the panel stack height) |
| `module` | all | see above | Module specs |
| `unfarmed_strip_m` | vertical | 0–3.0, default 1.0 | Strip under each vertical row that is not cropped |

Rules:

- A value outside its limits raises `ValueError` naming the field. The API turns this into a 422 error.
- A tracker whose lower panel edge would come within 0.3 m of the ground at `max_angle_deg` is rejected.
- Row spacing (pitch) is not an input. For each density, `pitch = collector_width_m / GCR`.
- Presets and the API translate "panels per row" into `collector_width_m` (2.278 m per panel in portrait,
  1.134 m in landscape) and fill `tilt_deg` with the district's optimum tilt limited to 10–25°.

### 5.2 Output

`simulate(weather, layout, losses=DEFAULT_LOSSES) -> PhysicsResult`

| Field | Shape | Meaning |
|---|---|---|
| `table` | `PhysicsTable` | `energy_kwh_per_kwp` and `light_fraction`, both 11 × 12 (density × month), and `ref_energy_kwh_per_acre`. Row 0 (GCR 0) is the open field: energy 0, light 1 |
| `light_darkest_tenth` | 11 × 12 | Light on the darkest tenth of the farmed strip, as a share of open field. The evenness figure; display only |
| `clear_gap_m` | 11 | Open ground between adjacent rows, for machinery. Row 0 is infinite |

### 5.3 Energy

For each hour and each density:

1. **Panel angle.** Fixed and vertical: as given. Tracker: the single-axis tracking equations of Anderson and
   Mikofski (2020) for a horizontal north–south axis, with backtracking for that density, limited to
   `max_angle_deg`.
2. **Light on the front.** The infinite-rows model of Mikofski et al. (2019), as in pvlib's `infinite_sheds`:
   - direct light, reduced by the share of the row width shaded by the row in front;
   - sky light split by the Hay–Davies model: the part near the sun is treated like direct light, and the rest
     is scaled by how much sky the row sees past the row in front;
   - light reflected from the ground (albedo 0.20), reduced by the shade on the ground.
3. **Light on the back** (bifacial only): the same model for the rear surface.
4. **Reflection loss.** The Martin–Ruiz incidence-angle model (`a_r = 0.16`) for direct light, and its diffuse
   form for sky and ground light.
5. **Effective light** = front + `bifaciality` × back × (1 − 0.05). The 5% is rear-side shading by the
   structure (assumption).
6. **Panel temperature.** Faiman model: `T_cell = T_air + G / (25 + 6.84 × wind)`.
7. **DC power** per kWp = `G_eff / 1000 × (1 + temp_coeff × (T_cell − 25))`, then DC losses.
8. **AC power**: PVWatts inverter model, DC/AC ratio 1.25, nominal efficiency 0.98, then AC losses.
9. Sum by month: `E[density, month]` in kWh per kWp.

**Losses** are fixed here before any comparison with reference data, and are not tuned to pass a check:

| Loss | Value | Basis |
|---|---|---|
| Soiling (dust) | 4% | Assumption for Indian conditions with regular cleaning |
| Mismatch | 1% | Assumption (PVWatts default is 2%; half-cut modules reduce it) |
| DC wiring | 1.5% | Assumption (PVWatts default 2%) |
| Connections | 0.5% | PVWatts default |
| AC wiring and transformer | 1.5% | Assumption |
| Inverter | PVWatts model, nominal 98% | Modern string and central inverters |
| DC/AC ratio | 1.25 | Common Indian practice (assumption) |

Combined, before inverter and clipping: 0.931 (DC) × 0.985 (AC). Plant downtime, first-year loss and yearly
degradation are **not** applied here. They are finance inputs in `apv_core` (`availability`, `degradation`).

**Reference plant for LER.** A conventional ground-mounted plant in the same district: fixed, south-facing,
tilt = optimum tilt limited to 10–25°, GCR 0.45, the same `module`. Its yearly energy per acre is
`ref_energy_kwh_per_acre`.

### 5.4 Ground light

The model is a cross-section across the rows, with rows repeating without end in both directions.

- The ground under one row spacing is split into **100 strips**.
- Each hour, a strip receives:
  - **direct light** (and the near-sun part of sky light), unless the line from the strip to the sun passes
    through a panel of any row;
  - **sky light**, scaled by the share of the sky dome the strip can see between the rows (a 2-D view factor).
    For fixed and vertical layouts this is computed once per density. For trackers it is computed on a 1°
    grid of panel angles and interpolated.
- **Farmed strip**: the whole row spacing for fixed and tracker layouts; for vertical layouts, the spacing
  minus `unfarmed_strip_m` centred under the row.
- `light_fraction[density, month]` = light summed over the farmed strips and the month's hours, divided by
  open-field light (GHI) over the same strips and hours.
- `light_darkest_tenth[density, month]` = the same ratio, taken over the tenth of farmed strips with the
  least light that month.

**What the model implies.** With endless rows, the *average* light on the ground and the energy per kWp
depend only on density, tilt and direction. Panel height and row width do not change them. They change
*where* the shade falls: taller or narrower rows spread it more evenly. So `height_m` and
`collector_width_m` affect `light_darkest_tenth` and `clear_gap_m`, plus cost and machinery access.

**Left out**, each on the cautious side or covered elsewhere:

- light reflected off panels or passing through gaps between modules (understates light slightly);
- extra light at the field edges of small plants (understates light);
- posts and tracks (covered by the farmable fraction `a_farm` in `apv_core`);
- any difference between the light crops use (PAR) and total sunlight (parent spec §12.1: a fixed share).

### 5.5 Speed

- Target: `simulate` for all 10 densities finishes in **0.6 s or less** for any layout on a current laptop.
  A test fails if it takes more than 2 s.
- The engine works on daylight hours only (about 4,400 rows) and on arrays, with no Python loop over hours.

### 5.6 Files

```
apv_physics/
  pyproject.toml
  README.md
  src/apv_physics/
    __init__.py       public names: Weather, Module, Layout, Losses, PhysicsResult, simulate, load_weather
    inputs.py         Weather, Module, Layout, Losses; limits and validation
    weather_io.py     load_weather(file) -> Weather
    tracking.py       tracker angle with backtracking
    irradiance.py     front and back light on the panel, reflection loss
    power.py          panel temperature, DC and AC power, losses
    ground.py         ground light: strip profile, mean and darkest tenth
    simulate.py       simulate(): loops over densities, builds PhysicsResult
  tests/
    data/             three committed sample weather packs (Jodhpur, Ernakulam, Leh)
```

## 6. Weather packs

**Builder:** `pipeline/src/pipeline/weather/build_packs.py`, run offline.

**Inputs** (all already in the repo or its local `raw/` folders):

- calibrated hourly files, `research/08_solar_weather/tmy/raw/pvgis_tmy_calibrated/*.csv.gz` (785 files);
- `research/08_solar_weather/tmy/tmy_index.csv` (district codes, point, elevation, file names);
- Global Solar Atlas optimum tilt at each point, sampled with `research/_scripts/sample_gsa_districts.py`.

**Steps, per district**

1. Read the hourly file. Use each time stamp as given: at zero offset the data satisfies (to three decimal places)
   `DNI × cos(zenith) + DHI = GHI` (checked on Jodhpur).
2. Compute apparent sun zenith and azimuth and extraterrestrial irradiance with pvlib.
3. Keep the hours where `ghi > 0`.
4. Write `data/weather/<stem>.npz` (numpy compressed), where `<stem>` is the existing file stem, such as
   `107_jodhpur`. District code alone is not unique (the code-0 districts).

**Pack contents**

| Array | Stored as | Scale |
|---|---|---|
| `month` | int8 | — |
| `ghi`, `dni`, `dhi`, `dni_extra` | int16 | × 10 |
| `temp_air`, `wind_speed` | int16 | × 10 |
| `zenith` | int16 | × 100 |
| `azimuth` | uint16 | × 100 |
| `meta` | JSON string | lat, lon, elevation, optimum tilt, district code and name, state, data version, attribution |

Measured size for Jodhpur: 37–71 KB, so roughly 30–50 MB for all districts.

**Index:** `data/weather/index.json`, one entry per district: code, name, state, file, point, optimum tilt,
annual GHI and DHI, and the file's SHA-256.

**Git:** `data/weather/*.npz` is git-ignored (binary, regenerated on each build). `index.json` is committed.
Three sample packs are committed under `apv_physics/tests/data/` so the tests run without the local raw data.

**Licence:** the packs are derived from PVGIS (use allowed with acknowledgement) and ERA5 (Copernicus licence:
redistribution allowed with attribution), scaled to the Global Solar Atlas (CC BY 4.0). Publishing them is a
change from keeping the hourly files local; the attribution in `SOURCE_pvgis_tmy.md` goes in each pack's
`meta` and on the Sources page.

## 7. Validation

| # | Check | Where it runs | Pass rule |
|---|---|---|---|
| V1 | Engine against pvlib, same weather and settings. Three sample districts × layouts (fixed at tilt 10° and 25°, facing 180° and 135°, monofacial and bifacial; tracker at 45° and 55°; vertical) × GCR 0.05, 0.25, 0.50 | `apv_physics` tests (pvlib is a test dependency) | Annual energy within ±1%; each month within ±2%; mean ground light within ±0.01 |
| V2 | Engine against the Global Solar Atlas at the 10 reference districts (`research/10_validation/energy_reference/energy_reference.csv`): monofacial, fixed, south, Atlas optimum tilt, GCR 0.05 | `pipeline` validation script (needs the local packs) | Annual energy within ±7% at every district |
| V3 | Engine against PySAM (PVWatts v8), same 10 districts, weather, tilt and losses | Same script (PySAM is a pipeline dependency) | Annual energy within ±3% at every district |
| V4 | Weather packs | Builder | 785 packs; annual GHI and DHI within 0.1% of `tmy_calibration.csv`; all values inside physical ranges |
| V5 | Speed (§5.5) | `apv_physics` tests | Under 2 s per layout |

V2 and V3 results are written to `data/validation/physics_validation.csv` and committed. The measured plants
(Pavagada and others) are listed there for information only, because their DC/AC ratios are unknown.

If V2 or V3 fails, the failure is reported with the numbers. The losses in §5.3 are changed only for a stated
physical reason, never to make a check pass.

## 8. Testing

Tests are written before the code they test.

**Known-answer tests**

- No rows in the way (GCR 0 row): energy 0 and light 1, exactly.
- Sun directly overhead, flat panels: the shaded share of the ground equals the density.
- A noon shadow's position and length match hand geometry for one layout.
- Flat panel, no wind, 25 °C cell, 1,000 W/m²: 1 kW DC per kWp before losses.
- Tracker at solar noon is flat; in the early morning with backtracking it does not shade the next row.

**Property tests** (Hypothesis, over random valid layouts on a sample pack)

- Light never rises as density rises.
- Mean light does not change with `height_m` or `collector_width_m` (within 0.005).
- `light_darkest_tenth` is never above `light_fraction`.
- Energy per kWp never rises as density rises (fixed layouts).
- Every output is finite, and light is within 0–1.
- Invalid inputs raise `ValueError` naming the field.

**Reference tests:** V1 and V5 above.

**Snapshot tests:** monthly energy and light for the three sample districts at one preset each, stored as
small CSV files, so accidental changes are caught.

## 9. Risks

| Risk | Effect | Handling |
|---|---|---|
| Our engine drifts from pvlib | Wrong energy or light | V1 runs on every change |
| Trackers are too slow (10× slower than fixed in pvlib) | Misses the 1.5 s request target | Sky view computed on a 1° angle grid; speed test V5 |
| PySAM uses a different sky model (Perez) | V3 may exceed ±3% in very diffuse climates | Report it; if it persists, document the cause and review the target with the owner |
| Endless-row model ignores field edges | Light understated for small plants | Stated on the Method page; errs on the cautious side |
| Weather packs published | Licence compliance | Attribution in every pack and on the Sources page (§6) |

## 10. Edits to the parent spec

| Section | Change |
|---|---|
| §7.3 Energy validation | "pvlib annual energy" becomes "the physics engine's annual energy"; add the ±1% engine-against-pvlib check |
| §8.4 REQ-MOD-02 | Presets become starting points; tilt and direction, height, row width and module specs are editable within limits |
| §8.17 REQ-PIP-04 | Precomputed physics is replaced by weather packs for every district, plus engine validation |
| §8.21 P2-05 | Custom geometry moves into v1; custom weather stays P2 |
| §9 A-5 | Fallback reworded: reduce the hourly data or cache results; still no pvlib at runtime |
| §11 | New `apv_physics` package; core decision becomes "weather offline, physics and economics live" |
| §12.1 | Rewritten to point here; the 110-layout grid is removed |
| §14.4 | `physics.parquet` is replaced by `weather/<stem>.npz` and `weather/index.json` |
| §15.1 | The pipeline uses pvlib and PySAM; the API uses numpy only, through `apv_physics` |
| §15.3 | The sweep request carries a layout object, not a configuration id |
| §15.4 | Physics tests as in §8 here |
| §18 | Phase 2 gains "weather packs and `apv_physics`" |

The app stays district-level. The editable settings describe a structure, not a site, so the non-goal on
site-level analysis (§4) stands.
