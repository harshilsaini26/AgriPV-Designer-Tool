# Model Slice Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy an API on Vercel that turns a district, a panel layout, crops and finance into the full density sweep, using the live physics engine and data already in the repo. The web pages are a second plan, written once this API's contract exists.

**Architecture:** An offline script (`pipeline.appdata`) builds small JSON files in `data/app/` from research CSVs. A FastAPI app in `backend/` loads them and the weather packs, resolves defaults, runs `apv_physics.simulate` then `apv_core.run_sweep`, and returns ranges with the source of every input. Vercel runs the app as one Python function; a placeholder Vite page proves that frontend and API share one domain.

**Tech Stack:** Python 3.12 on Vercel (code stays valid on 3.11), FastAPI ≥ 0.115, pydantic 2, numpy; pytest, httpx, ruff; Node 22 and Vite for the placeholder page.

**Spec:** [`docs/superpowers/specs/2026-11-15-model-slice-design.md`](../specs/2026-11-15-model-slice-design.md) (§5 app data, §6 API, §8 deployment, §9 testing)

## Global Constraints

- **Runtime dependencies of the API:** `fastapi`, `pydantic`, `numpy` only. No pandas, scipy or pvlib anywhere under `backend/`.
- **`apv_core` and `apv_physics` do not change.** The backend imports them from the repo through `backend/_paths.py`, which puts `apv_core/src` and `apv_physics/src` on `sys.path`.
- **Units:** yield in quintals per acre, price in ₹ per quintal, cost in ₹ per acre, tariff in ₹ per kWh, capex and O&M in ₹ per kWp. 1 hectare = 2.4711 acres.
- **Ranges in responses** are `{ "low", "central", "high" }`, mapped from `apv_core.Range(pessimistic, central, optimistic)`. Non-finite numbers are sent as `null`.
- **Every default** the API applies is reported in `inputs_used` with `value`, `source`, `year` and `flag`. Flags: `state`, `national_median`, `state_fallback`, `preset`, `interpolated`, `outside_benchmark_range`, `assumption`, `user`.
- **Assumption values** (spec §5, gap D21), exact: debt share 0.70, interest 0.10, loan 15 years, discount rate 0.09, degradation 0.005, availability 0.99, crop inflation 0.05, target IRR 0.12, lease ₹40,000 per acre per year, lease escalation 0.05. O&M escalation 0.0525 (from `capex_om_benchmarks.csv`).
- **Errors:** 404 for an unknown district; 422 with a FastAPI-style `detail` list (`loc`, `msg`, `type`) for every invalid value, including `ValueError`s from the engine; never a stack trace in a response.
- **JSON data files:** UTF-8, LF, `indent=1`, `ensure_ascii=False`, deterministic key order.
- **Tests first.** Style: ruff, line length 110. Commit messages end with `Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>`.
- **Run backend tests** from the repo root:
  `uv run --no-project --with fastapi --with httpx --with numpy --with pytest python -m pytest backend/tests -q`
- **Run pipeline tests:**
  `uv run --no-project --with-editable ./apv_core --with-editable ./apv_physics --with-editable "./pipeline[dev]" python -m pytest pipeline -q`
- **Work on branch** `feat/model-slice-backend`. Pushing it creates a Vercel preview.

## Review Focus

1. **A state with no economics data** (Ladakh, Goa and 15 others are not among the 19 states). Every crop must fall back to the national median and say so. *Test: Task 6 `test_state_without_economics_uses_national_median`.*
2. **Costs above crop value** (Maharashtra paddy: cost ₹33,068 against a value of ₹18,658 per acre). The sweep must return finite numbers and valid JSON, not NaN. *Test: Task 6 `test_loss_making_crop_returns_valid_json`.*
3. **A crop in a season it is not grown in**, two crops in one season, or an empty rotation. Each must be a 422 that names the rotation entry. *Test: Task 6 `test_rotation_errors_name_the_entry`.*
4. **Bad finance overrides:** a tariff of 0, a negative cost, an unknown field. Each must be a 422 naming the field. *Test: Task 7 `test_finance_errors_name_the_field`.*
5. **Data missing at start-up** (for example `data/app/` excluded from the Vercel bundle). The app must fail with a message naming the missing path, and `/api/health` must report the data version it loaded. *Test: Task 5 `test_missing_data_names_the_path`.*

---

## File Structure

```
app.py                          root shim for Vercel: from backend.app import app
requirements.txt                fastapi, pydantic, numpy
.python-version                 3.12
vercel.json                     build command for web/, function settings
backend/
  __init__.py
  _paths.py                     REPO_ROOT; puts apv_core/src and apv_physics/src on sys.path
  app.py                        FastAPI app, routes, exception handlers, frontend mount
  data.py                       AppData, load_app_data(), weather pack lookup
  schemas.py                    pydantic request and response models
  service.py                    resolve layout / rotation / finance; physics cache; run_sweep_request
  export_openapi.py             writes backend/openapi.json
  openapi.json                  committed contract snapshot
  tests/                        test_health.py test_read_endpoints.py test_sweep.py test_errors.py test_openapi.py
pipeline/src/pipeline/appdata/
  __init__.py
  states.py                     canonical_state()
  districts.py                  build_districts()
  crops.py                      build_crops()
  economics.py                  build_crop_economics()
  finance.py                    build_finance_defaults(), build_structures(), SOURCES
  build_app_data.py             CLI: writes data/app/*.json and manifest.json
pipeline/tests/                 test_appdata_states_districts_crops.py test_appdata_economics.py test_appdata_finance.py
data/app/                       districts.json crops.json crop_economics.json finance_defaults.json
                                structures.json sources.json manifest.json   (committed)
data/weather/*.npz              (now committed)
web/                            placeholder Vite + React + TS app (replaced by the web plan)
scripts/check_deployment.py     measures the spec §8 checks against any base URL
.github/workflows/backend.yml  pipeline.yml
```

---

### Task 1: Deployment test

**Files:**
- Create: `app.py`, `requirements.txt`, `.python-version`, `vercel.json`, `backend/__init__.py`, `backend/_paths.py`, `backend/app.py`, `backend/_probe.py`, `backend/tests/__init__.py`, `backend/tests/test_health.py`, `scripts/check_deployment.py`, `web/package.json`, `web/index.html`, `web/vite.config.ts`, `web/tsconfig.json`, `web/src/main.tsx`
- Modify: `.gitignore` (remove `data/weather/*.npz`; add `web/node_modules/`, `web/dist/`)
- Add to git: `data/weather/*.npz` (785 files)

**Interfaces:**
- Produces:
  - `backend._paths.REPO_ROOT: Path`; importing `backend._paths` makes `apv_core` and `apv_physics` importable.
  - `backend.app.app`: FastAPI instance with
    - `GET /api/health` → `{"status": "ok", "weather_packs": <int>, "python": "<version>"}`
    - `GET /api/_probe/sweep?district_id=<id>` → `{"district_id", "engine_ms": <float>, "ler_central": [11 floats], "allowed_gcr_central": <float|null>}`; 404 `{"detail": "unknown district"}` for an id with no weather pack. It runs `simulate` for a fixed 3 m bifacial layout (tilt = optimum tilt limited to 10–25°) and `run_sweep` with the hard-coded demo scenario in `backend/_probe.py` (bajra in kharif, wheat in rabi, KUSUM-A). **Temporary: removed in Task 6.**
    - When `web/dist` exists: `app.frontend("/", directory=<REPO_ROOT/web/dist>)`.
  - `scripts/check_deployment.py <base_url>` (stdlib only): requests `/`, `/model/107_jodhpur`, `/api/health`, then the probe once ("first") and 20 more times ("warm"); prints a table; exits 1 unless: `/` and the deep link return 200 HTML containing `AgriPV Lab`; health is `ok` with 785 packs; first probe ≤ 8.0 s; warm 95th percentile ≤ 1.5 s.
  - `web/`: a Vite + React + TypeScript app whose only page shows "AgriPV Lab — preview" and the result of `/api/health`. `npm run build` writes `web/dist`. The dev server proxies `/api` to `http://127.0.0.1:8000`.

- [ ] **Step 1: Create the branch.** `git checkout -b feat/model-slice-backend`

- [ ] **Step 2: Write the failing tests** `backend/tests/test_health.py`

```python
from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)


def test_health_reports_the_weather_packs():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["weather_packs"] == 785


def test_probe_runs_a_real_sweep():
    r = client.get("/api/_probe/sweep", params={"district_id": "107_jodhpur"})
    assert r.status_code == 200
    body = r.json()
    assert len(body["ler_central"]) == 11 and body["ler_central"][0] == 1.0
    assert body["engine_ms"] > 0


def test_probe_unknown_district_is_404():
    r = client.get("/api/_probe/sweep", params={"district_id": "nowhere"})
    assert r.status_code == 404 and r.json() == {"detail": "unknown district"}
```

- [ ] **Step 3: Run to verify they fail.** Expected: `ModuleNotFoundError: No module named 'backend'`.
- [ ] **Step 4: Implement** `backend/_paths.py`, `backend/_probe.py`, `backend/app.py`, root `app.py`, `requirements.txt` (`fastapi>=0.115`, `pydantic>=2`, `numpy>=1.26`) and `.python-version` (`3.12`). Demo scenario values in `_probe.py`: wheat `l_t` (0.93, 0.89, 0.76), `k` (1.36, 1.18, 1.10), grade A; bajra `l_t` (1.0, 1.0, 0.97), `k` (1.5, 1.32, 1.16), grade C; economics wheat (17.18, 2151, 15216), bajra (5.0, 2200, 9000); finance: capex 39,120, O&M 704, tariff 3.04, and the assumption values from Global Constraints; `a_farm` 0.92.
- [ ] **Step 5: Run the tests.** Expected: 3 passed.
- [ ] **Step 6: Create the placeholder web app** and build it: `cd web && npm install && npm run build`. Expected: `web/dist/index.html` exists.
- [ ] **Step 7: Check the wiring locally.** Start `uvicorn app:app --port 8000` (with `fastapi`, `uvicorn`, `numpy`), then run `python scripts/check_deployment.py http://127.0.0.1:8000`. Expected: all checks pass; note the warm 95th percentile.
- [ ] **Step 8: Write `vercel.json`** (primary configuration, spec §8):

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "buildCommand": "cd web && npm ci && npm run build",
  "functions": {
    "app.py": {
      "maxDuration": 30,
      "excludeFiles": "{research/**,docs/**,.github/**,web/node_modules/**,web/src/**,**/tests/**,pipeline/**}"
    }
  }
}
```

- [ ] **Step 9: Commit the weather packs and everything above**, then push the branch. Update `.gitignore` first. Commit message: `feat(backend): deployment test with a real sweep, placeholder page and weather packs`.
- [ ] **Step 10: Find the preview URL.** Look for Vercel's deployment on the pushed commit through GitHub's API (`/repos/harshilsaini26/AgriPV-Designer-Tool/commits/<sha>/status` and `/deployments?sha=<sha>`). On 2026-11-15 neither showed any Vercel activity for `main`, so if nothing appears within five minutes, stop and ask the owner for the Vercel project's URL and whether the GitHub integration is deploying this repo.
- [ ] **Step 11: Run `scripts/check_deployment.py <preview_url>`.** Expected: all checks pass.
- [ ] **Step 12: If a check fails**, record what failed, then try the fallbacks in order, one commit each, rerunning Step 11:
  1. File-based: delete root `app.py`; add `api/index.py` containing `from backend.app import app`; `vercel.json` gets `"outputDirectory": "web/dist"`, `"functions": {"api/index.py": {"maxDuration": 30, "includeFiles": "{backend/**,apv_core/src/**,apv_physics/src/**,data/app/**,data/weather/**}"}}` and `"rewrites": [{"source": "/api/(.*)", "destination": "/api/index"}, {"source": "/(.*)", "destination": "/index.html"}]`; drop the `app.frontend` call.
  2. Services: `"services": {"web": {"root": "web/"}, "api": {"root": ".", "entrypoint": "app:app"}}` with `"rewrites": [{"source": "/api/(.*)", "destination": {"service": "api"}}, {"source": "/(.*)", "destination": {"service": "web"}}]`, and no top-level `buildCommand` or `functions`.
  Build logs are only visible in the Vercel dashboard; ask the owner for the error text when a deployment fails without a reachable URL. If no configuration passes, stop and report.
- [ ] **Step 13: Record the result** in the spec (§8): which configuration works, bundle size if shown, first and warm response times. Commit: `docs: record the deployment test result`.

---

### Task 2: App data — states, districts, crops

**Files:**
- Create: `pipeline/src/pipeline/appdata/__init__.py`, `states.py`, `districts.py`, `crops.py`, `pipeline/tests/test_appdata_states_districts_crops.py`

**Interfaces:**
- Produces:
  - `states.canonical_state(name: str) -> str`: one spelling per state, in title case with lower-case "and"-style words kept as `&`: `"ODISHA"`, `"Orissa"` → `"Odisha"`; `"DADRA,NAGAR HAVELI,DAMAN & DIU"` → `"Dadra, Nagar Haveli, Daman & Diu"`; `"NCT of Delhi"`, `"DELHI"` → `"Delhi"`; `"Chattisgarh"` → `"Chhattisgarh"`; `"Uttaranchal"` → `"Uttarakhand"`; `"Pondicherry"` → `"Puducherry"`; `"ANDAMAN & NICOBAR"` → `"Andaman & Nicobar"`; `"JAMMU & KASHMIR"` → `"Jammu & Kashmir"`. Leading and trailing spaces ignored.
  - `districts.build_districts(index_entries: list[dict]) -> list[dict]`: one dict per entry with `id` (file name without `.npz`), `lgd`, `name`, `state` (canonical), `lat`, `lon`, `elevation_m`, `optimum_tilt_deg`; sorted by `state`, then `name`, then `id`. Raises `ValueError` on a duplicate `id`.
  - `crops.build_crops(param_rows: list[dict], bibliography_rows: list[dict]) -> list[dict]`, in the order of `param_rows`. Each: `id`, `name`, `seasons` (subset of `kharif`, `rabi`, `zaid`; "summer" means `zaid`; "whole year" gives `[]`), `tolerance`, `l_t` and `k` (each `{pessimistic, central, optimistic}` from the `_low`, `_central`, `_high` columns, or `null` when blank), `grade`, `n_studies`, `n_indian_studies`, `citations` (the bibliography `citation` for each id in `study_ids`, where `laub2022:<anything>` counts as `laub2022`, without repeats), `notes`, `selectable`, `not_selectable_reason`.
    - `tolerance`: `sensitive` if central `k` ≥ 1.3; `tolerant` if central `k` ≤ 0.9; otherwise `neutral`; `neutral` when there are no parameters.
    - `selectable` is false with reason `"whole-year crop: the model works by season"` when `seasons` is empty, and with reason `"not enough evidence (grade D)"` when the grade is D or the parameters are blank.
    - `name`: `rice` → "Rice", `gram` → "Gram (chickpea)", `mustard` → "Rapeseed & mustard", `bajra` → "Bajra (pearl millet)", `moong` → "Moong (green gram)", `tur` → "Tur (pigeon pea)", `jowar` → "Jowar (sorghum)", `urad` → "Urad (black gram)", `guar` → "Guar (cluster bean)", `sesame` → "Sesame (til)", others capitalised.

- [ ] **Step 1: Write the failing tests** `pipeline/tests/test_appdata_states_districts_crops.py`

```python
import csv
import json
from pathlib import Path

import pytest
from apv_core import CropParams, EvidenceGrade, Range, Season

from pipeline.appdata.crops import build_crops
from pipeline.appdata.districts import build_districts
from pipeline.appdata.states import canonical_state

REPO = Path(__file__).resolve().parents[2]
SHADE = REPO / "research" / "09_crop_shade_response"


def rows(path):
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@pytest.mark.parametrize("raw, want", [
    ("ODISHA", "Odisha"), ("Orissa", "Odisha"), (" RAJASTHAN ", "Rajasthan"), ("DELHI", "Delhi"),
    ("NCT of Delhi", "Delhi"), ("Chattisgarh", "Chhattisgarh"), ("JAMMU & KASHMIR", "Jammu & Kashmir"),
    ("DADRA,NAGAR HAVELI,DAMAN & DIU", "Dadra, Nagar Haveli, Daman & Diu"), ("Uttaranchal", "Uttarakhand"),
])  # fmt: skip
def test_canonical_state(raw, want):
    assert canonical_state(raw) == want


def test_districts_from_the_real_index():
    index = json.loads((REPO / "data" / "weather" / "index.json").read_text(encoding="utf-8"))["districts"]
    out = build_districts(index)
    assert len(out) == 785 and len({d["id"] for d in out}) == 785
    jodhpur = next(d for d in out if d["id"] == "107_jodhpur")
    assert jodhpur == {"id": "107_jodhpur", "lgd": "107", "name": "Jodhpur", "state": "Rajasthan",
                       "lat": 26.3522, "lon": 73.0996, "elevation_m": 222.0, "optimum_tilt_deg": 29.9}  # fmt: skip
    assert [d["state"] for d in out] == sorted(d["state"] for d in out)


def test_duplicate_district_id_is_an_error():
    entry = {"file": "1_x.npz", "dist_lgd": "1", "district": "X", "state": "GOA", "lat": 1.0, "lon": 2.0,
             "elevation_m": 3.0, "optimum_tilt_deg": 4.0}  # fmt: skip
    with pytest.raises(ValueError, match="1_x"):
        build_districts([entry, entry])


@pytest.fixture(scope="module")
def crops():
    built = build_crops(rows(SHADE / "parameters" / "crop_parameters_draft.csv"), rows(SHADE / "papers" / "bibliography.csv"))
    return {c["id"]: c for c in built}


def test_twenty_crops_in_file_order(crops):
    assert len(crops) == 20 and list(crops)[:3] == ["rice", "wheat", "soybean"]


def test_wheat(crops):
    w = crops["wheat"]
    assert w["seasons"] == ["rabi"] and w["grade"] == "A" and w["selectable"] is True
    assert w["l_t"] == {"pessimistic": 0.93, "central": 0.89, "optimistic": 0.76}
    assert w["k"] == {"pessimistic": 1.36, "central": 1.18, "optimistic": 1.1}
    assert w["tolerance"] == "neutral" and w["n_indian_studies"] == 2
    assert any("Laub" in c for c in w["citations"]) and len(w["citations"]) == len(set(w["citations"]))


def test_seasons_and_tolerance(crops):
    assert crops["rice"]["seasons"] == ["kharif", "rabi", "zaid"]
    assert crops["onion"]["seasons"] == ["kharif", "rabi"]
    assert crops["mustard"]["tolerance"] == "sensitive" and crops["cotton"]["tolerance"] == "tolerant"
    assert crops["gram"]["name"] == "Gram (chickpea)"


def test_crops_that_cannot_be_selected(crops):
    assert crops["sugarcane"]["selectable"] is False and "whole-year" in crops["sugarcane"]["not_selectable_reason"]
    assert crops["cumin"]["selectable"] is False and "grade D" in crops["cumin"]["not_selectable_reason"]
    assert crops["cumin"]["l_t"] is None and sum(c["selectable"] for c in crops.values()) == 18


def test_every_selectable_crop_is_valid_for_the_model(crops):
    for c in crops.values():
        if c["selectable"]:
            CropParams(c["id"], c["name"], frozenset(Season(s) for s in c["seasons"]), c["tolerance"],
                       Range(**c["l_t"]), Range(**c["k"]), EvidenceGrade(c["grade"]))  # fmt: skip
```

- [ ] **Step 2: Run to verify they fail.** Expected: `ModuleNotFoundError: pipeline.appdata`.
- [ ] **Step 3: Implement `states.py`, `districts.py`, `crops.py`.**
- [ ] **Step 4: Run the tests.** Expected: all pass.
- [ ] **Step 5: Commit.** `feat(pipeline): app data for districts and crops`

---

### Task 3: App data — crop economics

**Files:**
- Create: `pipeline/src/pipeline/appdata/economics.py`, `pipeline/tests/test_appdata_economics.py`

**Interfaces:**
- Consumes: `canonical_state` (Task 2)
- Produces:
  - `CROP_NAME_MAP: dict[str, str]` from the source's `crop_name` to our crop id: `Paddy` → `rice`, `Wheat` → `wheat`, `Soyabean` → `soybean`, `Cotton` → `cotton`, `Maize` → `maize`, `Gram` → `gram`, `Rapeseed & Mustard (Toria/Taramira)` → `mustard`, `Bajra` → `bajra`, `Sugarcane` → `sugarcane`, `Moong` → `moong`, `Groundnut` → `groundnut`, `Tur (Arhar)` → `tur`, `Jowar` → `jowar`, `Urad` → `urad`, `Potato` → `potato`, `Onion` → `onion`, `Masur` and `Lentil` → `lentil`, `Sesamum (Til)` → `sesame`.
  - `HECTARE_IN_ACRES = 2.4711`, `OLDEST_YEAR = "2018-19"`
  - `build_crop_economics(rows: list[dict]) -> dict` with keys:
    - `by_state`: `{state: {crop_id: {"yield_q_per_acre", "price_per_q", "cost_per_acre", "year", "basis": "state"}}}`
    - `national`: `{crop_id: {"yield_q_per_acre", "price_per_q", "cost_per_acre", "year", "basis": "national_median", "n_states"}}`
    - `source`: `"DES cost of cultivation (A2+FL), via India Data Portal"`
  - `build_example_rotations(rows: list[dict], crops: list[dict]) -> dict`: `{"by_state": {state: [{"season": "kharif", "crop_id"}, {"season": "rabi", "crop_id"}]}, "national": [...]}`. `crops` is `build_crops` output. For each state, among crops that are selectable and have a `by_state` entry, the kharif pick is the crop grown in kharif with the largest `num_holdings_sample` (from its latest usable row; blank counts as 0), and the rabi pick is the same among crops grown in rabi, excluding the kharif pick. A state with no pick for a season omits that entry. `national` uses the samples summed across states.
  - Rules: use a row only if `derived_yield`, `main_product_value` and `cul_cost_a2fl` are all present and positive and `year >= OLDEST_YEAR`. For each state and crop take the latest such year. Yield = `derived_yield / 2.4711` (2 decimals); price = `main_product_value / derived_yield` (whole ₹); cost = `cul_cost_a2fl / 2.4711` (whole ₹). The national entry is the median of each value across that crop's states, with `year` the most common year among them.

- [ ] **Step 1: Write the failing tests** `pipeline/tests/test_appdata_economics.py`

```python
import csv
from pathlib import Path

import pytest

from pipeline.appdata.economics import build_crop_economics

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "research" / "07_crop_economics" / "cost_of_cultivation" / "idp_des_cost_of_cultivation_1996-2022.csv"


def row(state, crop, year, y, value, cost):
    return {"state_name": state, "crop_name": crop, "year": year, "derived_yield": y,
            "main_product_value": value, "cul_cost_a2fl": cost}  # fmt: skip


def test_units_and_latest_year():
    out = build_crop_economics([
        row("Punjab", "Wheat", "2019-20", "40.0", "80000", "36000"),
        row("Punjab", "Wheat", "2021-22", "42.45", "91300.6", "37600.8"),
    ])  # fmt: skip
    assert out["by_state"]["Punjab"]["wheat"] == {
        "yield_q_per_acre": 17.18, "price_per_q": 2151, "cost_per_acre": 15216, "year": "2021-22", "basis": "state"}  # fmt: skip


def test_rows_that_are_old_incomplete_or_unmapped_are_ignored():
    out = build_crop_economics([
        row("Bihar", "Wheat", "2013-14", "30", "50000", "20000"),
        row("Bihar", "Maize", "2021-22", "30", "", "20000"),
        row("Bihar", "Jute", "2021-22", "30", "50000", "20000"),
    ])  # fmt: skip
    assert out["by_state"] == {} and out["national"] == {}


def test_national_median_and_state_names():
    out = build_crop_economics([
        row("ORISSA", "Paddy", "2021-22", "24.711", "49422", "24711"),
        row("Punjab", "Paddy", "2021-22", "74.133", "148266", "49422"),
        row("Bihar", "Paddy", "2020-21", "49.422", "98844", "74133"),
    ])  # fmt: skip
    assert set(out["by_state"]) == {"Odisha", "Punjab", "Bihar"}
    assert out["national"]["rice"] == {"yield_q_per_acre": 20.0, "price_per_q": 2000, "cost_per_acre": 20000,
                                       "year": "2021-22", "basis": "national_median", "n_states": 3}  # fmt: skip


def test_example_rotations_from_the_real_file():
    from pipeline.appdata.crops import build_crops
    from pipeline.appdata.economics import build_example_rotations

    shade = REPO / "research" / "09_crop_shade_response"
    with (shade / "parameters" / "crop_parameters_draft.csv").open(encoding="utf-8") as a, (
        shade / "papers" / "bibliography.csv"
    ).open(encoding="utf-8") as b, SOURCE.open(encoding="utf-8") as c:
        out = build_example_rotations(list(csv.DictReader(c)), build_crops(list(csv.DictReader(a)), list(csv.DictReader(b))))
    pair = lambda entries: [(e["season"], e["crop_id"]) for e in entries]  # noqa: E731
    assert pair(out["by_state"]["Rajasthan"]) == [("kharif", "bajra"), ("rabi", "wheat")]
    assert pair(out["by_state"]["Maharashtra"]) == [("kharif", "soybean"), ("rabi", "gram")]
    assert pair(out["by_state"]["Punjab"]) == [("kharif", "rice"), ("rabi", "wheat")]
    assert pair(out["national"]) == [("kharif", "rice"), ("rabi", "wheat")]
    assert all(e["crop_id"] != "sugarcane" for entries in out["by_state"].values() for e in entries)


def test_real_file_coverage():
    with SOURCE.open(encoding="utf-8") as fh:
        out = build_crop_economics(list(csv.DictReader(fh)))
    assert out["by_state"]["Punjab"]["wheat"]["yield_q_per_acre"] == pytest.approx(17.18)
    assert len(out["by_state"]) >= 19
    assert set(out["national"]) == {"rice", "wheat", "soybean", "cotton", "maize", "gram", "mustard", "bajra",
                                    "sugarcane", "moong", "groundnut", "tur", "jowar", "urad", "potato", "onion",
                                    "lentil", "sesame"}  # fmt: skip
```

- [ ] **Step 2: Run to verify they fail.** Expected: `ModuleNotFoundError: pipeline.appdata.economics`.
- [ ] **Step 3: Implement `economics.py`.**
- [ ] **Step 4: Run the tests.** Expected: all pass.
- [ ] **Step 5: Commit.** `feat(pipeline): state-level crop economics for the app`

---

### Task 4: App data — finance, structures, sources and the build command

**Files:**
- Create: `pipeline/src/pipeline/appdata/finance.py`, `pipeline/src/pipeline/appdata/build_app_data.py`, `pipeline/tests/test_appdata_finance.py`, `data/app/*.json` (outputs)

**Interfaces:**
- Consumes: Tasks 2–3; `kusum_a_state_tariffs.csv` (`state`, `tariff_inr_per_kwh`, `regulator_order`, `order_date`, `status`); `capex_om_benchmarks.csv` (`preset_id`, `capex_multiplier_central`, `capex_inr_per_kwp_dc_central|low|high`, `om_multiplier`, `om_inr_per_kwp_dc_yr1_central|low|high`, `om_escalation_pct_per_yr`, `price_year`); `structure_presets.csv` (`preset_id`, `clearance_m`, `hub_height_m`, `collector_width_m`, `a_farm_central|low|high`, `machinery_pass`, `din_spec_91434_category`); `module_parameters.csv`
- Produces:
  - `finance.ASSUMPTIONS: dict[str, float]` with the exact values in Global Constraints.
  - `finance.build_finance_defaults(tariff_rows, capex_rows) -> dict`:
    - `tariffs`: `{state: {"tariff_per_kwh", "order", "order_date", "status", "flag": "state"}}` for every row except `NATIONAL_FALLBACK`
    - `national_fallback`: `{"tariff_per_kwh": 3.11, "flag": "state_fallback"}`
    - `base_capex_per_kwp`, `base_om_per_kwp_year`: `{central, low, high}` from the `ground_fixed_reference` row
    - `om_escalation`: 0.0525; `price_year`: 2024
    - `assumptions`: `{name: {"value", "flag": "assumption"}}`
  - `finance.build_structures(preset_rows, module_rows, capex_rows) -> dict`:
    - `presets`: six entries (every preset except `ground_fixed_reference`), each `id`, `name`, `kind`, `tilt_rule` (`"optimum_10_25"` for fixed, else `null`), `azimuth_deg` (180 fixed, 90 vertical, `null` tracker), `height_m` (clearance for fixed and vertical, hub height for trackers), `collector_width_m`, `max_angle_deg` (55 for trackers, else `null`), `unfarmed_strip_m` (1.0 vertical, else 0.0), `module` (`"bifacial"`), `a_farm` `{central, low, high}`, `capex_multiplier`, `om_multiplier`, `machinery`, `din_category`
    - `modules`: `bifacial` `{efficiency: 0.225, bifaciality: 0.8, temp_coeff_per_c: -0.003}`, `monofacial` `{0.21, 0.0, -0.0035}`
    - `cost_points`: `{"fixed": [[2.5, 1.19], [3.0, 1.24], [4.0, 1.33]], "tracker": [[2.5, 1.29], [4.0, 1.4]], "vertical": [[0.8, 1.2]]}`
    - `limits`: the input limits of spec §5.1 of the physics design, as `{field: [low, high]}`
  - `finance.SOURCES: list[dict]`: `id`, `title`, `attribution`, `licence`, `url`, `used_for`, for: the weather packs (PVGIS, ERA5, Global Solar Atlas), crop shade parameters (Laub et al. 2022 and the papers in `bibliography.csv`), DES cost of cultivation, state tariff orders, MPERC 2024 cost norms, structure presets (DIN SPEC 91434 via Fraunhofer ISE), module datasheets, LGD district names, pvlib.
  - `build_app_data.main(repo: Path) -> dict`: writes the seven files of spec §5 to `<repo>/data/app/` (`crop_economics.json` also carries `example_rotation`, from `build_example_rotations`) and returns the manifest: `{"data_version": "2026-11-15", "files": {name: {"sha256", "count"}}}`. CLI: `python -m pipeline.appdata.build_app_data <repo_root>`.

- [ ] **Step 1: Write the failing tests** `pipeline/tests/test_appdata_finance.py`

```python
import csv
import json
import shutil
from pathlib import Path

from pipeline.appdata.build_app_data import main
from pipeline.appdata.finance import ASSUMPTIONS, SOURCES, build_finance_defaults, build_structures

REPO = Path(__file__).resolve().parents[2]
FIN = REPO / "research" / "11_finance_policy"
STRUCT = REPO / "research" / "12_structures_technology"


def rows(path):
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_finance_defaults():
    out = build_finance_defaults(rows(FIN / "kusum" / "kusum_a_state_tariffs.csv"), rows(FIN / "capex_om" / "capex_om_benchmarks.csv"))
    assert len(out["tariffs"]) == 11 and "NATIONAL_FALLBACK" not in out["tariffs"]
    assert out["tariffs"]["Rajasthan"]["tariff_per_kwh"] == 3.04 and out["tariffs"]["Rajasthan"]["flag"] == "state"
    assert out["national_fallback"] == {"tariff_per_kwh": 3.11, "flag": "state_fallback"}
    assert out["base_capex_per_kwp"] == {"central": 31550, "low": 28390, "high": 34700}
    assert out["base_om_per_kwp_year"]["central"] == 640 and out["om_escalation"] == 0.0525
    assert out["assumptions"]["interest_rate"] == {"value": 0.10, "flag": "assumption"}
    assert set(out["assumptions"]) == set(ASSUMPTIONS)


def test_structures():
    out = build_structures(rows(STRUCT / "structure_presets.csv"), rows(STRUCT / "module_parameters.csv"),
                           rows(FIN / "capex_om" / "capex_om_benchmarks.csv"))  # fmt: skip
    by_id = {p["id"]: p for p in out["presets"]}
    assert list(by_id) == ["elevated_fixed_2.5m", "elevated_fixed_3m", "elevated_fixed_4m", "tracker_2.5m",
                           "tracker_4m", "vertical_bifacial_ew"]  # fmt: skip
    fixed = by_id["elevated_fixed_3m"]
    assert (fixed["kind"], fixed["height_m"], fixed["collector_width_m"], fixed["tilt_rule"]) == ("fixed", 3.0, 4.56, "optimum_10_25")
    assert fixed["a_farm"] == {"central": 0.92, "low": 0.9, "high": 0.95} and fixed["capex_multiplier"] == 1.24
    tracker = by_id["tracker_4m"]
    assert (tracker["kind"], tracker["height_m"], tracker["max_angle_deg"], tracker["azimuth_deg"]) == ("tracker", 4.0, 55.0, None)
    vertical = by_id["vertical_bifacial_ew"]
    assert (vertical["kind"], vertical["azimuth_deg"], vertical["unfarmed_strip_m"]) == ("vertical", 90.0, 1.0)
    assert out["modules"]["bifacial"] == {"efficiency": 0.225, "bifaciality": 0.8, "temp_coeff_per_c": -0.003}
    assert out["cost_points"]["fixed"] == [[2.5, 1.19], [3.0, 1.24], [4.0, 1.33]]
    assert out["limits"]["height_m"] == [0.5, 6.0] and out["limits"]["tilt_deg"] == [0.0, 40.0]


def test_sources_cover_what_the_app_shows():
    ids = {s["id"] for s in SOURCES}
    assert {"weather", "crop_shade", "crop_economics", "tariffs", "costs", "structures", "pvlib"} <= ids
    assert all(s["attribution"] and s["licence"] for s in SOURCES)


def test_build_writes_all_files(tmp_path):
    for part in ("research", "data/weather/index.json"):
        src, dst = REPO / part, tmp_path / part
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("raw", "*.pdf", "*.xls", "*.shp", "*.dbf"))
        else:
            shutil.copy2(src, dst)
    manifest = main(tmp_path)
    app = tmp_path / "data" / "app"
    assert {p.name for p in app.iterdir()} == {"districts.json", "crops.json", "crop_economics.json", "finance_defaults.json",
                                                "structures.json", "sources.json", "manifest.json"}  # fmt: skip
    assert manifest["files"]["districts.json"]["count"] == 785 and manifest["files"]["crops.json"]["count"] == 20
    assert json.loads((app / "manifest.json").read_text(encoding="utf-8")) == manifest
    assert b"\r\n" not in (app / "crops.json").read_bytes()
    economics = json.loads((app / "crop_economics.json").read_text(encoding="utf-8"))
    assert economics["example_rotation"]["by_state"]["Rajasthan"][0] == {"season": "kharif", "crop_id": "bajra"}
```

- [ ] **Step 2: Run to verify they fail.** Expected: `ModuleNotFoundError`.
- [ ] **Step 3: Implement `finance.py` and `build_app_data.py`.**
- [ ] **Step 4: Run the tests.** Expected: all pass.
- [ ] **Step 5: Build the real files.** Run the CLI on the repo. Expected: seven files in `data/app/`; read `crop_economics.json` and `finance_defaults.json` once for sanity.
- [ ] **Step 6: Commit** the code and `data/app/`. `feat(pipeline): finance defaults, structures, sources and the app data build`

---

### Task 5: API — data loading and the read endpoints

**Files:**
- Create: `backend/data.py`, `backend/schemas.py`, `backend/tests/test_read_endpoints.py`
- Modify: `backend/app.py`

**Interfaces:**
- Consumes: `data/app/*.json` (Task 4), `data/weather/*.npz`
- Produces:
  - `backend.data.AppData` (frozen dataclass): `districts: dict[str, dict]`, `crops: dict[str, dict]`, `economics: dict`, `finance: dict`, `structures: dict`, `sources: list[dict]`, `manifest: dict`
  - `backend.data.load_app_data(root: Path | None = None) -> AppData`, cached for the default root. Raises `RuntimeError("app data is missing: <path>")` naming the first missing file.
  - `backend.data.economics_for(app: AppData, state: str, crop_id: str) -> dict | None`: the state entry, else the national entry, else `None`.
  - `backend.data.tariff_for(app: AppData, state: str) -> dict`: the state tariff entry or the national fallback.
  - `backend.data.example_rotation_for(app: AppData, state: str) -> dict`: `{"basis": "state" | "national", "crops": [{"season", "crop_id"}, ...]}`; the state's pair when it has both seasons, otherwise the national pair.
  - `backend.data.weather_path(district_id: str) -> Path` under `data/weather/`.
  - `PREVIEW_NOTICE = "Preview: crop shade parameters are draft, crop economics are state-level figures for 2021-22, and loan terms are assumptions."`
  - Routes (response models in `schemas.py`):
    - `GET /api/health` → adds `"data_version"`.
    - `GET /api/meta` → `data_version`, `preview_notice`, `presets`, `modules`, `limits`, `crops`, `seasons` (`["kharif", "rabi", "zaid"]`), `policy` (`{"default": 0.8, "min": 0.5, "max": 1.0, "step": 0.05}`), `retention_bases` (`["per_acre_of_land", "per_cropped_area"]`), `business_models` (`["kusum_a", "lease"]`), `assumptions`, `sources`.
    - `GET /api/districts` → list of `{id, name, state}`, in the stored order.
    - `GET /api/district/{district_id}` → the district entry plus `default_tilt_deg` (optimum tilt limited to 10–25), `tariff` (from `tariff_for`), `economics` (`{crop_id: entry}` for every crop with one, through `economics_for`), `example_rotation` (from `example_rotation_for`). 404 `{"detail": "unknown district"}`.

- [ ] **Step 1: Write the failing tests** `backend/tests/test_read_endpoints.py`

```python
import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.data import load_app_data

client = TestClient(app)


def test_meta():
    m = client.get("/api/meta").json()
    assert m["data_version"] and m["preview_notice"].startswith("Preview")
    assert len(m["presets"]) == 6 and len(m["crops"]) == 20
    assert m["policy"] == {"default": 0.8, "min": 0.5, "max": 1.0, "step": 0.05}
    assert m["limits"]["height_m"] == [0.5, 6.0] and m["seasons"] == ["kharif", "rabi", "zaid"]
    assert m["assumptions"]["interest_rate"]["flag"] == "assumption"
    assert any(s["id"] == "weather" for s in m["sources"])


def test_districts_list():
    d = client.get("/api/districts").json()
    assert len(d) == 785 and set(d[0]) == {"id", "name", "state"}


def test_district_with_a_state_tariff():
    d = client.get("/api/district/107_jodhpur").json()
    assert d["name"] == "Jodhpur" and d["state"] == "Rajasthan" and d["default_tilt_deg"] == 25.0
    assert d["tariff"]["tariff_per_kwh"] == 3.04 and d["tariff"]["flag"] == "state"
    assert d["economics"]["bajra"]["basis"] == "state" and "guar" not in d["economics"]
    assert d["example_rotation"] == {"basis": "state", "crops": [{"season": "kharif", "crop_id": "bajra"},
                                                              {"season": "rabi", "crop_id": "wheat"}]}  # fmt: skip


def test_district_with_fallbacks():
    d = client.get("/api/district/9_leh_ladakh").json()
    assert d["tariff"] == {"tariff_per_kwh": 3.11, "flag": "state_fallback"}
    assert d["economics"]["wheat"]["basis"] == "national_median"
    assert d["example_rotation"]["basis"] == "national"
    assert [c["crop_id"] for c in d["example_rotation"]["crops"]] == ["rice", "wheat"]


def test_unknown_district_is_404():
    r = client.get("/api/district/nowhere")
    assert r.status_code == 404 and r.json() == {"detail": "unknown district"}


def test_health_reports_the_data_version():
    assert client.get("/api/health").json()["data_version"] == load_app_data().manifest["data_version"]


def test_missing_data_names_the_path(tmp_path):
    with pytest.raises(RuntimeError, match="districts.json"):
        load_app_data(tmp_path)
```

- [ ] **Step 2: Run to verify they fail.** Expected: `ModuleNotFoundError: backend.data`.
- [ ] **Step 3: Implement `data.py`, the response models and the routes.**
- [ ] **Step 4: Run the backend tests.** Expected: all pass (Task 1's tests included).
- [ ] **Step 5: Commit.** `feat(backend): app data loading, meta, districts and district endpoints`

---

### Task 6: API — the sweep

**Files:**
- Create: `backend/service.py`, `backend/tests/test_sweep.py`
- Modify: `backend/schemas.py`, `backend/app.py` (add `POST /api/sweep`; remove the probe route), `scripts/check_deployment.py` (use `POST /api/sweep`); delete `backend/_probe.py`; `backend/tests/test_health.py` (drop the two probe tests)

**Interfaces:**
- Consumes: Task 5; `apv_physics` (`Kind`, `Layout`, `Module`, `load_weather`, `simulate`); `apv_core` (`BusinessModel`, `CropEconomics`, `CropParams`, `EvidenceGrade`, `FinanceInputs`, `METRIC_KEYS`, `Range`, `RetentionBasis`, `Season`, `SeasonCrop`, `Structure`, `SweepInputs`, `run_sweep`)
- Produces:
  - Request models (pydantic, `extra="forbid"`): `SweepRequest(district_id: str, business_model: Literal["kusum_a", "lease"], layout: LayoutIn, a_farm: float | None, rotation: list[RotationIn], finance: FinanceIn = {}, policy_limit: float = 0.8, retention_basis: Literal[...] = "per_acre_of_land", land_acres: float | None)`; `LayoutIn(preset_id: str | None, kind: Literal["fixed", "tracker", "vertical"], tilt_deg, azimuth_deg, height_m, collector_width_m, max_angle_deg, unfarmed_strip_m: float | None, module: ModuleIn | None)`; `RotationIn(season: Literal["kharif", "rabi", "zaid"], crop_id: str, economics: EconomicsIn | None)`; `FinanceIn`: every `FinanceInputs` field except `years`, all optional.
  - `service.resolve_layout(layout: LayoutIn, district: dict, app: AppData) -> tuple[Layout, list[dict]]`: start from the preset when `preset_id` is given (else from `kind` alone with: fixed height 3.0, width 4.56; tracker height 2.5, width 2.28, max angle 55; vertical height 0.8, width 2.27, strip 1.0), fixed tilt defaults to the district's `default_tilt_deg`, module defaults to bifacial; then apply the fields the request sets. The list holds `inputs_used` entries for the layout, with `flag` `preset` for untouched preset values and `user` for overridden ones.
  - `service.cost_multiplier(kind: str, height_m: float, cost_points: dict) -> tuple[float, str]`: linear interpolation between that kind's points; flag `preset` on an exact point, `interpolated` between points, `outside_benchmark_range` (value held at the nearest point) beyond them.
  - `service.resolve_finance(finance: FinanceIn, district: dict, layout: Layout, app: AppData) -> tuple[FinanceInputs, list[dict]]`: capex = base capex × `cost_multiplier`; O&M = base O&M × the preset's `om_multiplier` (1.1 fixed, 1.2 tracker, 1.0 vertical when there is no preset); tariff from `tariff_for`; the rest from the assumptions; request values override and are flagged `user`.
  - `service.resolve_rotation(rotation: list[RotationIn], district: dict, app: AppData) -> tuple[tuple[SeasonCrop, ...], list[dict]]`. Raises `InputError(loc, message)` (a `ValueError` subclass carrying a `loc` tuple) for: an empty rotation (`("rotation",)`); an unknown or non-selectable crop (`("rotation", i, "crop_id")`); a crop not grown in that season (`("rotation", i, "season")`); a repeated season (`("rotation", i, "season")`); no economics available and none given (`("rotation", i, "economics")`).
  - `service.physics_for(district_id: str, layout: Layout) -> PhysicsResult`, `functools.lru_cache(maxsize=64)`.
  - `service.build_sweep_inputs(req: SweepRequest) -> tuple[SweepInputs, PhysicsResult, list[dict], bool]`: the model inputs, the physics result, the `inputs_used` list and whether the layout is custom. Raises `LookupError` for an unknown district (the route turns it into the 404).
  - `inputs_used` entries are `{"name", "value", "flag", "source", "year"}`. Names: `layout.<field>`, `a_farm`, `finance.<field>`, `rotation.<season>.<crop_id>.<field>`. `source` is a short label: the tariff entry's `order` text; `"DES cost of cultivation"` for crop economics; `"MPERC 2024 cost norms x structure multiplier"` for capex and O&M; `"optimum tilt limited to 10-25 degrees"` for a defaulted tilt; `"structure preset"` for other preset values; `"assumption"`; `"entered by the user"`. `year` is an integer (the order's year, 2021 for crop year 2021-22 economics, 2024 for costs) or `null`.
  - `service.run_sweep_request(req: SweepRequest) -> dict` matching `SweepResponse`: `gcr`, `metrics` (`{key: [{low, central, high} × 11]}` for every `METRIC_KEYS` entry), `retention` (`{season: [range × 11]}`), `retention_basis`, `light` (`{season: {"mean": [11], "darkest_tenth": [11]}}`, each the average over that season's months), `clear_gap_m` (11, `null` for the open field), `allowed_gcr` (range), `outside_policy` (11 booleans), `baseline_farm_income`, `notices` (`[{code, message, gcr, gcrs}]`), `inputs_used`, `custom_layout` (bool), `data_version`, `engine_ms`.
  - `a_farm` defaults to the preset's central value, or 0.92 / 0.90 / 0.88 (fixed / tracker / vertical) without a preset; allowed range 0.5–1.0.

- [ ] **Step 1: Write the failing tests** `backend/tests/test_sweep.py`

```python
import json
import math

import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.service import cost_multiplier, physics_for

client = TestClient(app)
BASE = {
    "district_id": "107_jodhpur",
    "business_model": "kusum_a",
    "layout": {"preset_id": "elevated_fixed_3m", "kind": "fixed"},
    "rotation": [{"season": "kharif", "crop_id": "bajra"}, {"season": "rabi", "crop_id": "wheat"}],
}


def post(**changes):
    return client.post("/api/sweep", json={**BASE, **changes})


def used(body, name):
    return next(i for i in body["inputs_used"] if i["name"] == name)


def test_default_sweep_shape():
    r = post()
    assert r.status_code == 200
    b = r.json()
    assert b["gcr"] == [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]
    assert {"farm_income", "energy_income", "ler", "project_irr", "kwp_per_acre"} <= set(b["metrics"])
    assert all(len(v) == 11 for v in b["metrics"].values())
    assert set(b["retention"]) == {"kharif", "rabi"} == set(b["light"])
    assert b["metrics"]["ler"][0] == {"low": 1.0, "central": 1.0, "high": 1.0}
    assert b["metrics"]["farm_income"][0]["central"] == pytest.approx(b["baseline_farm_income"])
    assert b["light"]["rabi"]["mean"][0] == 1.0 and b["clear_gap_m"][0] is None
    assert b["light"]["rabi"]["darkest_tenth"][5] <= b["light"]["rabi"]["mean"][5] < 1.0
    assert b["custom_layout"] is False and b["engine_ms"] > 0 and b["data_version"]


def test_defaults_are_reported_with_their_source():
    b = post().json()
    tariff = used(b, "finance.tariff_per_kwh")
    assert set(tariff) == {"name", "value", "flag", "source", "year"}
    assert (tariff["value"], tariff["flag"], tariff["year"]) == (3.04, "state", 2025) and tariff["source"].startswith("RERC")
    assert used(b, "finance.interest_rate")["flag"] == "assumption"
    assert used(b, "finance.capex_per_kwp")["value"] == pytest.approx(31550 * 1.24)
    assert used(b, "layout.tilt_deg") == {"name": "layout.tilt_deg", "value": 25.0, "flag": "preset",
                                          "source": "optimum tilt limited to 10-25 degrees", "year": None}  # fmt: skip
    assert used(b, "rotation.kharif.bajra.yield_q_per_acre")["flag"] == "state"
    assert used(b, "rotation.rabi.wheat.yield_q_per_acre")["year"] == 2021


def test_overrides_are_flagged_and_change_the_result():
    base = post().json()
    b = post(finance={"tariff_per_kwh": 4.0}, layout={**BASE["layout"], "height_m": 3.5}).json()
    assert used(b, "finance.tariff_per_kwh")["flag"] == "user" and b["custom_layout"] is True
    assert used(b, "finance.capex_per_kwp")["flag"] == "interpolated"
    assert b["metrics"]["energy_income"][5]["central"] > base["metrics"]["energy_income"][5]["central"]
    # height changes how even the light is, not its mean
    assert b["light"]["rabi"]["mean"] == pytest.approx(base["light"]["rabi"]["mean"], abs=0.005)


def test_matches_a_direct_model_call():
    from apv_core import run_sweep

    from backend.schemas import SweepRequest
    from backend.service import build_sweep_inputs

    direct = run_sweep(build_sweep_inputs(SweepRequest(**BASE))[0])
    b = post().json()
    for key in ("ler", "farm_income", "project_irr"):
        assert b["metrics"][key][5]["central"] == pytest.approx(direct.metrics[key][5].central)
    assert b["allowed_gcr"]["central"] == direct.allowed_gcr.central


def test_physics_is_reused_when_only_finance_changes():
    post()
    hits = physics_for.cache_info().hits
    post(finance={"tariff_per_kwh": 3.5}, policy_limit=0.7)
    assert physics_for.cache_info().hits == hits + 1


def test_user_economics_and_lease():
    b = post(business_model="lease",
             rotation=[{"season": "kharif", "crop_id": "guar",
                        "economics": {"yield_q_per_acre": 4.0, "price_per_q": 5000, "cost_per_acre": 8000}}]).json()  # fmt: skip
    assert b["metrics"]["max_affordable_lease"][6]["central"] is not None
    assert any(n["code"] == "user_entered_values" for n in b["notices"])
    assert used(b, "rotation.kharif.guar.price_per_q")["flag"] == "user"


def test_state_without_economics_uses_national_median():
    b = post(district_id="9_leh_ladakh", rotation=[{"season": "rabi", "crop_id": "wheat"}]).json()
    assert used(b, "rotation.rabi.wheat.yield_q_per_acre")["flag"] == "national_median"
    assert used(b, "finance.tariff_per_kwh")["flag"] == "state_fallback"


def test_loss_making_crop_returns_valid_json():
    r = post(district_id="490_pune", rotation=[{"season": "kharif", "crop_id": "rice"}])
    assert r.status_code == 200
    json.loads(r.text, parse_constant=lambda c: pytest.fail(f"non-finite number in the response: {c}"))
    b = r.json()
    assert b["baseline_farm_income"] < 0
    assert all(v["central"] is None or math.isfinite(v["central"]) for v in b["metrics"]["farm_income"])


def test_rotation_errors_name_the_entry():
    cases = [
        ([], ["body", "rotation"]),
        ([{"season": "kharif", "crop_id": "wheat"}], ["body", "rotation", 0, "season"]),
        ([{"season": "kharif", "crop_id": "sugarcane"}], ["body", "rotation", 0, "crop_id"]),
        ([{"season": "kharif", "crop_id": "guar"}], ["body", "rotation", 0, "economics"]),
        ([{"season": "kharif", "crop_id": "bajra"}, {"season": "kharif", "crop_id": "maize"}], ["body", "rotation", 1, "season"]),
    ]  # fmt: skip
    for rotation, loc in cases:
        r = post(rotation=rotation)
        assert r.status_code == 422 and r.json()["detail"][0]["loc"] == loc, rotation


def test_unknown_district_is_404():
    assert post(district_id="nowhere").status_code == 404


def test_cost_multiplier():
    points = {"fixed": [[2.5, 1.19], [3.0, 1.24], [4.0, 1.33]], "vertical": [[0.8, 1.2]]}
    assert cost_multiplier("fixed", 3.0, points) == (1.24, "preset")
    assert cost_multiplier("fixed", 3.5, points) == (pytest.approx(1.285), "interpolated")
    assert cost_multiplier("fixed", 5.0, points) == (1.33, "outside_benchmark_range")
    assert cost_multiplier("vertical", 2.0, points) == (1.2, "outside_benchmark_range")
```

- [ ] **Step 2: Check the fixture facts before running.** Confirm with a two-line script that `490_pune` is in Maharashtra in `data/app/districts.json` and that Maharashtra rice has a cost above its value (yield × price) in `crop_economics.json`. Both were true of the source data on 2026-11-15.
- [ ] **Step 3: Run to verify they fail.** Expected: `ModuleNotFoundError: backend.service`.
- [ ] **Step 4: Implement the request and response models, `service.py` and the route**; remove the probe; point `scripts/check_deployment.py` at `POST /api/sweep` with the `BASE` body.
- [ ] **Step 5: Run the backend tests.** Expected: all pass.
- [ ] **Step 6: Commit.** `feat(backend): the sweep endpoint with resolved defaults and a physics cache`

---

### Task 7: API — errors, contract snapshot, CI, documents, deployed check

**Files:**
- Create: `backend/export_openapi.py`, `backend/openapi.json`, `backend/tests/test_errors.py`, `backend/tests/test_openapi.py`, `.github/workflows/backend.yml`, `.github/workflows/pipeline.yml`
- Modify: `backend/app.py` (exception handlers), `PRODUCT.md`, the parent spec §15.3, `research/08_solar_weather/tmy/SOURCE_pvgis_tmy.md`, the slice spec §8

**Interfaces:**
- Produces:
  - Exception handlers on `app`: `InputError` → 422 `{"detail": [{"loc": ["body", *loc], "msg": message, "type": "value_error"}]}`; any other `ValueError` raised while building `Layout`, `Module`, `Structure`, `CropEconomics`, `FinanceInputs` or `SweepInputs` → 422 with `loc` `["body", <section>, <field>]`, where the field is the name the message starts with (`"height_m must be within ..."` → `["body", "layout", "height_m"]`) and the section is `layout`, `finance` or `rotation`; anything else → 500 `{"detail": "internal error"}` with the traceback logged, not returned.
  - `python -m backend.export_openapi` writes `backend/openapi.json` (`indent=1`, sorted keys, LF).

- [ ] **Step 1: Write the failing tests** `backend/tests/test_errors.py` and `backend/tests/test_openapi.py`

```python
# test_errors.py
import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.tests.test_sweep import BASE

client = TestClient(app, raise_server_exceptions=False)


def loc_of(**changes):
    r = client.post("/api/sweep", json={**BASE, **changes})
    assert r.status_code == 422, r.text
    return r.json()["detail"][0]["loc"]


def test_layout_errors_name_the_field():
    assert loc_of(layout={"kind": "fixed", "height_m": 9.0}) == ["body", "layout", "height_m"]
    assert loc_of(layout={"kind": "tracker", "height_m": 1.0, "collector_width_m": 2.28}) == ["body", "layout", "height_m"]
    assert loc_of(layout={"kind": "fixed", "module": {"efficiency": 0.5, "bifaciality": 0.8,
                                                      "temp_coeff_per_c": -0.003}})[:3] == ["body", "layout", "module"]  # fmt: skip


def test_finance_errors_name_the_field():
    assert loc_of(finance={"tariff_per_kwh": 0}) == ["body", "finance", "tariff_per_kwh"]
    assert loc_of(finance={"capex_per_kwp": -5}) == ["body", "finance", "capex_per_kwp"]
    assert loc_of(finance={"tarif": 3.0}) == ["body", "finance", "tarif"]


def test_policy_and_farmable_fraction_limits():
    assert loc_of(policy_limit=0.3) == ["body", "policy_limit"]
    assert loc_of(a_farm=1.4) == ["body", "a_farm"]


def test_unexpected_failure_is_a_plain_500(monkeypatch):
    import backend.service as service

    monkeypatch.setattr(service, "physics_for", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    r = client.post("/api/sweep", json=BASE)
    assert r.status_code == 500 and r.json() == {"detail": "internal error"} and "boom" not in r.text
```

```python
# test_openapi.py
import json
from pathlib import Path

from backend.app import app


def test_committed_contract_is_current():
    committed = json.loads((Path(__file__).resolve().parents[1] / "openapi.json").read_text(encoding="utf-8"))
    assert app.openapi() == committed, "run: python -m backend.export_openapi"
```

- [ ] **Step 2: Run to verify they fail.** Expected: failures in the error-shape tests and a missing `openapi.json`.
- [ ] **Step 3: Implement the handlers and `export_openapi.py`; generate `openapi.json`.**
- [ ] **Step 4: Run all backend and pipeline tests, and ruff on `backend`, `scripts`, `app.py` and `pipeline`.** Expected: all pass, no findings.
- [ ] **Step 5: Add the two CI workflows.** `backend.yml`: on changes to `backend/**`, `apv_core/**`, `apv_physics/**`, `data/app/**`, `requirements.txt`, `app.py`; Python 3.12; `pip install -r requirements.txt pytest httpx ruff`; `ruff check backend scripts app.py`; `pytest backend/tests`. `pipeline.yml`: on changes to `pipeline/**`, `research/**/*.csv`; `pip install -e apv_core -e apv_physics -e "pipeline[dev]"`; `ruff check pipeline`; `pytest pipeline`.
- [ ] **Step 6: Update the documents** listed in spec §12: `PRODUCT.md` (physics is calculated live), parent spec §15.3 (`GET /api/districts`, the sweep fields), the weather source card (packs are committed and public).
- [ ] **Step 7: Commit and push.** `feat(backend): error handling, contract snapshot and CI`
- [ ] **Step 8: Run `scripts/check_deployment.py <preview_url>`** against the new preview. Expected: all checks pass with the real sweep. Record the first and warm times in the slice spec §8 and commit.
