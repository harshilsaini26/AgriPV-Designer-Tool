# Live Physics Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `apv_physics`, a numpy-only engine that turns one district's hourly weather and a user-entered panel layout into monthly energy, ground light and light evenness for every GCR, plus the offline script that builds each district's weather pack.

**Architecture:** `pipeline.weather` (offline, uses pvlib) writes one compressed `.npz` weather pack per district holding calibrated hourly irradiance, temperature, wind and precomputed sun positions. `apv_physics` (live, numpy only) loads a pack and simulates a layout: tracker angle → panel irradiance (infinite-rows model ported from pvlib) → reflection loss → temperature → DC/AC power, and a strip-by-strip ground-light model. It returns the `PhysicsTable` that `apv_core.run_sweep` already consumes. pvlib and PySAM appear only in tests and the offline validation script.

**Tech Stack:** Python ≥ 3.11, numpy, `apv_core`; dev/test: pytest, Hypothesis, ruff, pvlib 0.16.1; pipeline: pandas, pvlib, `nrel-pysam` (validation only).

**Spec:** [`docs/superpowers/specs/2026-11-14-live-physics-design.md`](../specs/2026-11-14-live-physics-design.md) (parent: [`2026-11-06-agripv-lab-product-spec.md`](../specs/2026-11-06-agripv-lab-product-spec.md) §11, §12.1)

## Global Constraints

- **Runtime imports:** nothing under `apv_physics/src/` may import pandas, scipy or pvlib. Runtime dependencies are `numpy>=1.26` and `apv_core` only.
- **pvlib is pinned** to `==0.16.1` in dev dependencies. Ported functions must match that version.
- **Ported code** (from `pvlib/bifacial/utils.py`, `pvlib/bifacial/infinite_sheds.py`, `pvlib/iam.py`) carries pvlib's BSD 3-Clause notice in `apv_physics/NOTICE` and a one-line credit in each module docstring.
- **Units:** angles in degrees; irradiance W/m²; temperature °C; wind m/s; energy kWh per kWp; lengths m. Azimuth 0 = north, clockwise. All arrays float64 unless stated.
- **Grid:** densities are `apv_core.constants.GCR_GRID` (11 values, row 0 = GCR 0). Output arrays are 11 × 12 (density × month, month `m` at index `m − 1`). Row 0 is exactly energy 0 and light 1.
- **Losses** (spec §5.3), exact values: soiling 0.04, mismatch 0.01, DC wiring 0.015, connections 0.005, AC wiring 0.015, inverter nominal efficiency 0.98 (reference efficiency 0.9637), DC/AC ratio 1.25, rear shading 0.05, albedo 0.20. Never tune them to pass a check.
- **Reflection loss:** Martin–Ruiz, `a_r = 0.16`. **Temperature:** Faiman, `u0 = 25.0`, `u1 = 6.84`.
- **Input limits** (spec §5.1): tilt 0–40; azimuth 90–270; tracker max angle 30–60; height 0.5–6.0; collector width 0.5–10.0; unfarmed strip 0–3.0; module efficiency 0.15–0.25, bifaciality 0–0.95, temperature coefficient −0.005 to −0.002. Violations raise `ValueError` whose message starts with the field name.
- **Tests first.** Every test is written and seen to fail before its code exists.
- **Style:** ruff, line length 110, target py311; LF line endings; type hints on public functions.
- **Git:** never commit `data/weather/*.npz` or anything under `research/**/raw/`. Commit messages end with `Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>`.
- **Run tests** from the repo root:
  `uv run --no-project --with-editable ./apv_core --with-editable "./apv_physics[dev]" python -m pytest apv_physics -q`

## Review Focus

1. **Sun on the horizon or in the panel plane.** Zenith 89.99° with the sun square to the rows makes `tan φ` huge; a vertical panel with the sun exactly in its plane makes the shaded-fraction formula divide by zero. Outputs must stay finite and within range. *Test: Task 6 `test_no_nan_at_grazing_sun`, Task 8 `test_grazing_sun_is_finite`.*
2. **Tracker with the sun along the axis or overhead.** Azimuth exactly 180° or zenith 0 gives a true-tracking angle of 0 and `sign(0)` in the backtracking step. The result must be 0, not NaN. *Test: Task 4 `test_sun_on_axis_gives_flat`.*
3. **A month with no daylight rows.** A pack that lacks a month must give energy 0 and light 1 for that month, with no division by zero. *Test: Task 9 `test_missing_month_is_safe`.*
4. **Layout corners inside the limits.** Width 0.5 m at height 6 m (many rows in view), width 10 m at height 0.5 m, tilt 0 at GCR 0.50, tilt 40 facing east. All must run, stay finite and meet the speed limit. *Test: Task 9 `test_limit_corners`.*
5. **Vertical rows with a wide unfarmed strip.** Collector width 0.5 m with a 3 m strip leaves no farmed ground at GCR 0.50 (pitch 1 m). This must raise a `ValueError` naming `unfarmed_strip_m`, not return NaN. *Test: Task 8 `test_no_farmed_ground_raises`.*

---

## File Structure

```
apv_physics/
  pyproject.toml            package metadata; deps numpy, apv_core; dev extras
  README.md                 what the engine does, inputs, outputs, how to test
  NOTICE                    pvlib BSD 3-Clause notice for ported code
  src/apv_physics/
    __init__.py             public names
    inputs.py               Kind, Module, Layout, Losses, Weather; limits and validation
    weather_io.py           save_weather, load_weather, load_meta (the pack format)
    tracking.py             tracker_rotation
    viewfactors.py          ported pvlib 2-D view factors
    irradiance.py           iam_beam, iam_diffuse, panel_irradiance, effective_irradiance
    power.py                cell_temperature, dc_power_per_kwp, ac_power_per_kwp
    ground.py               strip_unshaded, strip_sky_view, farmed_mask, ground_light
    simulate.py             PhysicsResult, simulate, reference_energy_kwh_per_acre
  tests/
    data/                   107_jodhpur.npz, 555_ernakulam.npz, 9_leh_ladakh.npz; snapshots/*.csv
    reference.py            the same chain built from pvlib calls (test-only)
    helpers.py              shared weather() builder for tests
    test_inputs.py  test_weather_io.py  test_tracking.py  test_viewfactors.py
    test_irradiance.py  test_power.py  test_ground.py  test_simulate.py
    test_properties.py  test_against_pvlib.py  test_snapshots.py
pipeline/
  pyproject.toml            deps numpy, pandas, pvlib, apv_physics; extra "validation" = nrel-pysam
  src/pipeline/__init__.py
  src/pipeline/weather/__init__.py
  src/pipeline/weather/build_packs.py       calibrated CSV → weather packs + index.json
  src/pipeline/validation/__init__.py
  src/pipeline/validation/physics_validation.py   engine vs Global Solar Atlas and PySAM
  tests/test_build_packs.py
research/_scripts/gsa_opt_tilt_districts.py      Atlas optimum tilt at each district point
research/08_solar_weather/tmy/tmy_opt_tilt.csv   (output, committed)
data/weather/index.json                          (output, committed)
data/validation/physics_validation.csv           (output, committed)
.github/workflows/apv_physics.yml
```

---

### Task 1: Package scaffold and inputs

**Files:**
- Create: `apv_physics/pyproject.toml`, `apv_physics/NOTICE`, `apv_physics/src/apv_physics/__init__.py`, `apv_physics/src/apv_physics/inputs.py`, `apv_physics/tests/helpers.py`, `apv_physics/tests/test_inputs.py`, `.github/workflows/apv_physics.yml`

**Interfaces:**
- Consumes: `apv_core.constants.GCR_GRID`
- Produces (all in `apv_physics.inputs`, re-exported from `apv_physics`):
  - `class Kind(StrEnum)`: `FIXED = "fixed"`, `TRACKER = "tracker"`, `VERTICAL = "vertical"`
  - `@dataclass(frozen=True) class Module(efficiency: float, bifaciality: float, temp_coeff_per_c: float)`
  - `BIFACIAL = Module(0.225, 0.80, -0.0030)`, `MONOFACIAL = Module(0.210, 0.0, -0.0035)`
  - `@dataclass(frozen=True) class Layout(kind: Kind, module: Module, height_m: float, collector_width_m: float, tilt_deg: float = 0.0, azimuth_deg: float = 180.0, max_angle_deg: float = 55.0, unfarmed_strip_m: float = 1.0)`. `kind` accepts the string value. Only the fields that apply to `kind` are validated (spec §5.1 table).
  - `Layout.center_height_m -> float`: fixed `height_m + collector_width_m / 2 × sin(tilt)`; vertical `height_m + collector_width_m / 2`; tracker `height_m`.
  - `@dataclass(frozen=True) class Losses(soiling=0.04, mismatch=0.01, dc_wiring=0.015, connections=0.005, ac_wiring=0.015, inverter_efficiency=0.98, dc_ac_ratio=1.25, rear_shading=0.05, albedo=0.20)` with properties `dc_factor` (product of `1 − x` over the four DC losses) and `ac_factor` (`1 − ac_wiring`).
  - `@dataclass(frozen=True) class Weather(month, ghi, dni, dhi, temp_air, wind_speed, zenith, azimuth, dni_extra, latitude: float, longitude: float, elevation_m: float, optimum_tilt_deg: float)`. Arrays are converted to read-only float64 (`month` to int8), must share one length ≥ 1 and be finite; `month` within 1–12; `ghi`, `dni`, `dhi` ≥ 0.

- [ ] **Step 1: Write the failing tests.** `apv_physics/tests/helpers.py` holds the shared `weather()` builder; `apv_physics/tests/test_inputs.py` holds the tests.

```python
# tests/helpers.py
import numpy as np

from apv_physics import Weather


def weather(n=3, **kw):
    base = dict(month=np.ones(n), ghi=np.full(n, 500.0), dni=np.full(n, 600.0), dhi=np.full(n, 100.0),
                temp_air=np.full(n, 25.0), wind_speed=np.full(n, 2.0), zenith=np.full(n, 40.0),
                azimuth=np.full(n, 180.0), dni_extra=np.full(n, 1360.0), latitude=26.0, longitude=73.0,
                elevation_m=220.0, optimum_tilt_deg=27.0)  # fmt: skip
    base.update(kw)
    return Weather(**base)
```

```python
# tests/test_inputs.py
import numpy as np
import pytest
from helpers import weather

from apv_physics import BIFACIAL, MONOFACIAL, Kind, Layout, Losses, Module


def fixed(**kw):
    base = dict(kind=Kind.FIXED, module=BIFACIAL, height_m=3.0, collector_width_m=4.56, tilt_deg=20.0)
    base.update(kw)
    return Layout(**base)


def test_presets():
    assert BIFACIAL == Module(0.225, 0.80, -0.0030)
    assert MONOFACIAL == Module(0.210, 0.0, -0.0035)


def test_kind_accepts_string():
    assert fixed(kind="fixed").kind is Kind.FIXED


@pytest.mark.parametrize(
    "field, value",
    [("tilt_deg", 40.1), ("tilt_deg", -1.0), ("azimuth_deg", 89.0), ("azimuth_deg", 271.0),
     ("height_m", 0.4), ("height_m", 6.1), ("collector_width_m", 0.4), ("collector_width_m", 10.1)],
)  # fmt: skip
def test_fixed_limits_name_the_field(field, value):
    with pytest.raises(ValueError, match=f"^{field}"):
        fixed(**{field: value})


def test_tracker_limits():
    Layout(Kind.TRACKER, BIFACIAL, height_m=2.5, collector_width_m=2.28, max_angle_deg=55.0)
    with pytest.raises(ValueError, match="^max_angle_deg"):
        Layout(Kind.TRACKER, BIFACIAL, height_m=2.5, collector_width_m=2.28, max_angle_deg=61.0)
    with pytest.raises(ValueError, match="^height_m"):  # lower edge within 0.3 m of the ground at full turn
        Layout(Kind.TRACKER, BIFACIAL, height_m=1.0, collector_width_m=2.28, max_angle_deg=55.0)


def test_tracker_ignores_fixed_only_fields():
    Layout(Kind.TRACKER, BIFACIAL, height_m=2.5, collector_width_m=2.28, tilt_deg=99.0)


def test_vertical_strip_limit():
    with pytest.raises(ValueError, match="^unfarmed_strip_m"):
        Layout(Kind.VERTICAL, BIFACIAL, height_m=0.8, collector_width_m=2.27, azimuth_deg=90.0, unfarmed_strip_m=3.5)


@pytest.mark.parametrize("args", [(0.14, 0.8, -0.003), (0.22, 0.96, -0.003), (0.22, 0.8, -0.001)])
def test_module_limits(args):
    with pytest.raises(ValueError):
        Module(*args)


def test_center_height():
    assert fixed().center_height_m == pytest.approx(3.0 + 2.28 * np.sin(np.radians(20.0)))
    assert Layout(Kind.VERTICAL, BIFACIAL, 0.8, 2.27, azimuth_deg=90.0).center_height_m == pytest.approx(1.935)
    assert Layout(Kind.TRACKER, BIFACIAL, 2.5, 2.28).center_height_m == 2.5


def test_loss_factors():
    assert Losses().dc_factor == pytest.approx(0.93146328)
    assert Losses().ac_factor == pytest.approx(0.985)


def test_weather_arrays_are_readonly_float():
    w = weather()
    assert w.ghi.dtype == np.float64 and w.month.dtype == np.int8
    with pytest.raises(ValueError):
        w.ghi[0] = 1.0


@pytest.mark.parametrize("kw", [{"ghi": np.array([1.0, 2.0])}, {"month": np.array([0, 1, 2])},
                                {"dni": np.array([1.0, np.nan, 2.0])}, {"dhi": np.array([-1.0, 0.0, 0.0])}])  # fmt: skip
def test_weather_validation(kw):
    with pytest.raises(ValueError):
        weather(**kw)
```

- [ ] **Step 2: Run to verify they fail.** Expected: `ModuleNotFoundError: No module named 'apv_physics'`.
- [ ] **Step 3: Create `pyproject.toml`** modelled on `apv_core/pyproject.toml`: name `apv_physics`, version `0.1.0`, `dependencies = ["numpy>=1.26", "apv_core"]`, `dev = ["pytest>=8", "hypothesis>=6.100", "ruff>=0.6", "pvlib==0.16.1"]`, the same setuptools, pytest (`testpaths = ["tests"]`, `pythonpath = ["tests"]`) and ruff settings.
- [ ] **Step 4: Create `NOTICE`** stating that `viewfactors.py` and `irradiance.py` contain code adapted from pvlib-python 0.16.1, followed by pvlib's BSD 3-Clause licence text (copy from the installed package's `LICENSE`).
- [ ] **Step 5: Implement `inputs.py` and `__init__.py`** to the Interfaces block.
- [ ] **Step 6: Run the tests.** Expected: all pass.
- [ ] **Step 7: Add `.github/workflows/apv_physics.yml`**, a copy of `apv_core.yml` with paths `apv_core/**`, `apv_physics/**` and the workflow file; install step `pip install -e apv_core -e "apv_physics[dev]"`; then `ruff check apv_physics` and `pytest apv_physics`.
- [ ] **Step 8: Commit.** `feat(apv_physics): package scaffold, layout and weather inputs`

---

### Task 2: Weather pack format

**Files:**
- Create: `apv_physics/src/apv_physics/weather_io.py`, `apv_physics/tests/test_weather_io.py`

**Interfaces:**
- Consumes: `Weather` (Task 1)
- Produces (in `apv_physics.weather_io`; `load_weather` re-exported from `apv_physics`):
  - `PACK_VERSION = 1`
  - `save_weather(weather: Weather, meta: dict, file) -> None`: `np.savez_compressed` with arrays `month` (int8); `ghi`, `dni`, `dhi`, `dni_extra`, `temp_air`, `wind_speed` (int16, value × 10, rounded); `zenith` (int16, × 100); `azimuth` (uint16, × 100); and `meta`, a JSON string. `meta` always gains `pack_version`, `latitude`, `longitude`, `elevation_m`, `optimum_tilt_deg` from `weather`; caller keys (district, state, attribution, data version) are kept.
  - `load_weather(file) -> Weather`: reverses the scaling. `file` is a path or a binary file object. Raises `ValueError("unsupported weather pack version")` when `pack_version != 1`.
  - `load_meta(file) -> dict`

- [ ] **Step 1: Write the failing tests** `apv_physics/tests/test_weather_io.py`

```python
import io
import json

import numpy as np
import pytest
from helpers import weather

from apv_physics.weather_io import load_meta, load_weather, save_weather


def test_round_trip_within_quantisation():
    w = weather(ghi=np.array([0.04, 512.34, 1099.96]), zenith=np.array([12.344, 45.0, 89.996]),
                azimuth=np.array([0.0, 181.237, 359.99]), temp_air=np.array([-12.34, 25.0, 47.96]))  # fmt: skip
    buf = io.BytesIO()
    save_weather(w, {"district": "Test", "attribution": "x"}, buf)
    buf.seek(0)
    r = load_weather(buf)
    np.testing.assert_allclose(r.ghi, w.ghi, atol=0.05)
    np.testing.assert_allclose(r.zenith, w.zenith, atol=0.005)
    np.testing.assert_allclose(r.azimuth, w.azimuth, atol=0.005)
    np.testing.assert_allclose(r.temp_air, w.temp_air, atol=0.05)
    assert (r.latitude, r.optimum_tilt_deg) == (26.0, 27.0)
    np.testing.assert_array_equal(r.month, w.month)


def test_meta_is_kept_and_extended():
    buf = io.BytesIO()
    save_weather(weather(), {"district": "Test"}, buf)
    buf.seek(0)
    meta = load_meta(buf)
    assert meta["district"] == "Test" and meta["pack_version"] == 1 and meta["elevation_m"] == 220.0


def test_load_from_path(tmp_path):
    p = tmp_path / "x.npz"
    save_weather(weather(), {}, p)
    assert load_weather(p).ghi.shape == (3,)


def test_unknown_version_rejected(tmp_path):
    p = tmp_path / "x.npz"
    save_weather(weather(), {}, p)
    d = dict(np.load(p))
    d["meta"] = np.array(json.dumps({**json.loads(str(d["meta"])), "pack_version": 2}))
    np.savez_compressed(p, **d)
    with pytest.raises(ValueError, match="unsupported weather pack version"):
        load_weather(p)
```

- [ ] **Step 2: Run to verify they fail.** Expected: `ModuleNotFoundError: apv_physics.weather_io`.
- [ ] **Step 3: Implement `weather_io.py`** to the Interfaces block; export `load_weather` from `__init__.py`.
- [ ] **Step 4: Run the tests.** Expected: all pass.
- [ ] **Step 5: Commit.** `feat(apv_physics): weather pack save and load`

---

### Task 3: Build the weather packs

**Files:**
- Create: `research/_scripts/gsa_opt_tilt_districts.py`, `pipeline/pyproject.toml`, `pipeline/src/pipeline/__init__.py`, `pipeline/src/pipeline/weather/__init__.py`, `pipeline/src/pipeline/weather/build_packs.py`, `pipeline/tests/test_build_packs.py`
- Create (outputs): `research/08_solar_weather/tmy/tmy_opt_tilt.csv`, `data/weather/index.json`, `apv_physics/tests/data/{107_jodhpur,555_ernakulam,9_leh_ladakh}.npz`
- Modify: `.gitignore` (add `data/weather/*.npz`), `research/08_solar_weather/tmy/SOURCE_pvgis_tmy.md` (files and processing notes: packs, optimum tilt, public redistribution with attribution)

**Interfaces:**
- Consumes: `save_weather`, `Weather` (Tasks 1–2); `research/_scripts/sample_gsa_districts.py` (`ZIP`, `sample(zf, name, pts) -> (values, counts)`); `tmy_index.csv` columns `dist_lgd, district, state, lat, lon, elevation_m, file, status`; calibrated files with columns `time_utc` (`%Y%m%d:%H%M`), `ghi, dni, dhi, temp_air, wind_speed`
- Produces:
  - `tmy_opt_tilt.csv`: columns `dist_lgd, district, file, gsa_opt_tilt_deg, opt_tilt_source` (`gsa`, or `latitude` where the Atlas has no value; then the tilt is `abs(lat)`). `file` is the stem, e.g. `107_jodhpur`.
  - `pipeline.weather.build_packs`:
    - `ATTRIBUTION`: the attribution string from `SOURCE_pvgis_tmy.md` plus "calibrated to Global Solar Atlas 2 (Solargis / World Bank, CC BY 4.0)"
    - `make_weather(df: pd.DataFrame, lat: float, lon: float, elevation_m: float, optimum_tilt_deg: float) -> Weather`: sun position at each stamp as given (`pvlib.solarposition.get_solarposition(times, lat, lon, altitude=elevation_m)`: `apparent_zenith`, `azimuth`), `pvlib.irradiance.get_extra_radiation(times)`, then keeps rows with `ghi > 0`
    - `build_all(research_dir: Path, out_dir: Path) -> list[dict]`: writes `<out_dir>/<stem>.npz` for every `status == "ok"` row and `<out_dir>/index.json`; each entry has `dist_lgd, district, state, file, lat, lon, elevation_m, optimum_tilt_deg, opt_tilt_source, n_hours, ghi_kwh_m2_yr, dhi_kwh_m2_yr, sha256`. Raises `RuntimeError` listing every district whose annual GHI or DHI differs from `tmy_calibration.csv` (`ghi_after_kwh_m2_yr`, `dhi_after_kwh_m2_yr`) by more than `max(0.1 %, 1 kWh/m²)`, or whose pack count is not the number of `ok` rows.
    - CLI: `python -m pipeline.weather.build_packs <research_dir> <out_dir>`

- [ ] **Step 1: Write the failing tests** `pipeline/tests/test_build_packs.py`

```python
import numpy as np
import pandas as pd

from pipeline.weather.build_packs import make_weather


def frame():
    # one June day at Jodhpur, hourly UTC stamps; irradiance filled from a simple clear-sky shape
    t = pd.date_range("2019-06-21 00:00", periods=24, freq="h", tz="UTC")
    ghi = np.clip(1000 * np.sin(np.pi * (np.arange(24) - 0.5) / 13.5), 0, None)
    ghi[14:] = 0.0
    return pd.DataFrame({"time_utc": t.strftime("%Y%m%d:%H%M"), "ghi": ghi, "dni": ghi * 0.8, "dhi": ghi * 0.3,
                         "temp_air": 35.0, "wind_speed": 2.0})  # fmt: skip


def test_keeps_daylight_rows_only():
    w = make_weather(frame(), 26.35, 73.10, 222.0, 27.0)
    assert len(w.ghi) == int((frame()["ghi"] > 0).sum())
    assert (w.ghi > 0).all() and set(w.month.tolist()) == {6}


def test_sun_position_is_plausible():
    w = make_weather(frame(), 26.35, 73.10, 222.0, 27.0)
    i = int(np.argmin(w.zenith))
    assert w.zenith[i] < 6.0  # near-overhead at the June solstice, close to the tropic
    assert 1300 < w.dni_extra[0] < 1340  # Earth is far from the sun in June
    assert w.optimum_tilt_deg == 27.0 and w.elevation_m == 222.0
```

- [ ] **Step 2: Run to verify they fail.** Run: `uv run --no-project --with-editable ./apv_core --with-editable ./apv_physics --with-editable "./pipeline[dev]" python -m pytest pipeline -q`. Expected: `ModuleNotFoundError: pipeline`.
- [ ] **Step 3: Create `pipeline/pyproject.toml`** (name `pipeline`, deps `numpy>=1.26`, `pandas>=2`, `pvlib==0.16.1`, `apv_physics`; extras `dev = ["pytest>=8", "ruff>=0.6"]`, `validation = ["nrel-pysam>=5"]`; same pytest and ruff settings) and the package `__init__` files.
- [ ] **Step 4: Implement `make_weather` and run the tests.** Expected: pass.
- [ ] **Step 5: Write `research/_scripts/gsa_opt_tilt_districts.py`** in the style of `energy_reference.py`: read `tmy_index.csv`, sample layer `"OPTA"` at each point with `sample(...)[0]`, write `tmy_opt_tilt.csv` (values rounded to 0.1). Run it: `uv run --no-project --with numpy python -I research/_scripts/gsa_opt_tilt_districts.py research`. Expected: 785 rows; Jodhpur 29.9, Leh 34.3.
- [ ] **Step 6: Implement `build_all` and the CLI**, add `data/weather/*.npz` to `.gitignore`, then run `python -m pipeline.weather.build_packs research data/weather`. Expected: 785 packs, no `RuntimeError`, total folder size printed (expect 30–60 MB).
- [ ] **Step 7: Copy the three sample packs** into `apv_physics/tests/data/` and update `SOURCE_pvgis_tmy.md`.
- [ ] **Step 8: Commit.** `feat(pipeline): build per-district weather packs` (commit `index.json`, `tmy_opt_tilt.csv`, the three sample packs, scripts and the source card; not the 785 packs).

---

### Task 4: Tracker angle

**Files:**
- Create: `apv_physics/src/apv_physics/tracking.py`, `apv_physics/tests/test_tracking.py`

**Interfaces:**
- Produces: `tracker_rotation(zenith, azimuth, gcr: float, max_angle_deg: float) -> np.ndarray`. Horizontal north–south axis. Signed degrees: **positive faces west** (surface azimuth 270), negative faces east. Zero where `zenith >= 90`.
  - `θ_T = atan2(sin Z · sin(A − 180°), cos Z)`
  - backtracking: `t = |cos θ_T| / gcr`; where `t < 1`, `θ = θ_T − sign(θ_T) · arccos(t)`, else `θ = θ_T`
  - clip to `±max_angle_deg`

- [ ] **Step 1: Write the failing tests** `apv_physics/tests/test_tracking.py`

```python
import numpy as np
import pvlib
import pytest

from apv_physics import load_weather
from apv_physics.tracking import tracker_rotation

DATA = __import__("pathlib").Path(__file__).parent / "data"


@pytest.mark.parametrize(
    "zen, az, expected",
    [(30.0, 180.0, 0.0), (80.0, 90.0, -15.7293), (60.0, 110.0, -55.0), (70.0, 260.0, 39.79)],
)
def test_hand_values(zen, az, expected):
    assert tracker_rotation(np.array([zen]), np.array([az]), 0.4, 55.0)[0] == pytest.approx(expected, abs=1e-3)


def test_sun_on_axis_gives_flat():
    out = tracker_rotation(np.array([0.0, 45.0, 45.0]), np.array([123.0, 180.0, 0.0]), 0.3, 55.0)
    np.testing.assert_allclose(out, 0.0, atol=1e-9)


def test_below_horizon_is_zero():
    assert tracker_rotation(np.array([95.0]), np.array([80.0]), 0.3, 55.0)[0] == 0.0


def test_backtracking_keeps_rows_out_of_each_others_shade():
    # with no turning limit, the row shadow never reaches past the next row:
    # gcr * cos(theta - theta_true) <= |cos(theta_true)|
    w = load_weather(DATA / "107_jodhpur.npz")
    true = np.degrees(np.arctan2(np.sin(np.radians(w.zenith)) * np.sin(np.radians(w.azimuth - 180.0)),
                                 np.cos(np.radians(w.zenith))))  # fmt: skip
    theta = tracker_rotation(w.zenith, w.azimuth, 0.4, 90.0)
    assert (0.4 * np.cos(np.radians(theta - true)) <= np.abs(np.cos(np.radians(true))) + 1e-9).all()


@pytest.mark.parametrize("gcr", [0.05, 0.25, 0.5])
def test_matches_pvlib_on_a_real_year(gcr):
    w = load_weather(DATA / "107_jodhpur.npz")
    ref = pvlib.tracking.singleaxis(w.zenith, w.azimuth, axis_tilt=0, axis_azimuth=180, max_angle=55,
                                    backtrack=True, gcr=gcr)["tracker_theta"]  # fmt: skip
    np.testing.assert_allclose(tracker_rotation(w.zenith, w.azimuth, gcr, 55.0), np.nan_to_num(ref), atol=1e-6)
```

- [ ] **Step 2: Run to verify they fail.** Expected: `ModuleNotFoundError: apv_physics.tracking`.
- [ ] **Step 3: Implement `tracker_rotation`** from the three formulas above.
- [ ] **Step 4: Run the tests.** Expected: all pass.
- [ ] **Step 5: Commit.** `feat(apv_physics): single-axis tracker angle with backtracking`

---

### Task 5: View factors (ported)

**Files:**
- Create: `apv_physics/src/apv_physics/viewfactors.py`, `apv_physics/tests/test_viewfactors.py`

**Interfaces:**
- Produces: numpy-only ports of these pvlib 0.16.1 functions from `pvlib/bifacial/utils.py`, with the same parameters, defaults and return shapes (leading underscore dropped; `vectorize` and pandas handling removed):
  - `solar_projection_tangent(solar_zenith, solar_azimuth, surface_azimuth)`
  - `unshaded_ground_fraction(tracker_rotation, phi, gcr, height=None, pitch=None, max_rows=10, max_zenith=85, g0=0, g1=1)`
  - `vf_ground_sky_2d(rotation, gcr, x, pitch, height, max_rows=10)`
  - `vf_ground_sky_2d_integ(tracker_rotation, gcr, height, pitch, max_rows=10, npoints=100)`
  - `vf_row_sky_2d_integ(surface_tilt, gcr, x0=0, x1=1)`
  - `vf_row_ground_2d_integ(surface_tilt, gcr, height=None, pitch=None, x0=0, x1=1, max_rows=20, g0=0, g1=1)`
  - plus the private helpers they call (`_vf_poly`, `_obstructed_string_lengths`, `_dist`, `_angle`, and `pvlib.tools` `sind`, `cosd`, `tand`, `atand`).

- [ ] **Step 1: Write the failing tests** `apv_physics/tests/test_viewfactors.py`

```python
import numpy as np
import pytest
from pvlib.bifacial import utils as pv

from apv_physics import viewfactors as vf

TILTS = [0.0, 10.0, 25.0, 55.0, 90.0, 125.0, 170.0]
GCRS = [0.05, 0.25, 0.5]


@pytest.mark.parametrize("gcr", GCRS)
def test_row_view_factors_match_pvlib(gcr):
    t = np.array(TILTS)
    np.testing.assert_allclose(vf.vf_row_sky_2d_integ(t, gcr), pv.vf_row_sky_2d_integ(t, gcr), rtol=1e-9)
    np.testing.assert_allclose(vf.vf_row_ground_2d_integ(t, gcr), pv.vf_row_ground_2d_integ(t, gcr), rtol=1e-9)


@pytest.mark.parametrize("gcr", GCRS)
@pytest.mark.parametrize("height", [0.75, 3.0, 6.0])
def test_ground_sky_view_matches_pvlib(gcr, height):
    pitch = 4.56 / gcr
    rot = np.array([-55.0, -20.0, 0.0, 20.0, 55.0, 90.0])
    x = np.linspace(0.005, 0.995, 100)
    np.testing.assert_allclose(vf.vf_ground_sky_2d(rot, gcr, x, pitch, height),
                               pv.vf_ground_sky_2d(rot, gcr, x, pitch, height), rtol=1e-9)  # fmt: skip
    np.testing.assert_allclose(vf.vf_ground_sky_2d_integ(rot, gcr, height, pitch),
                               pv.vf_ground_sky_2d_integ(rot, gcr, height, pitch), rtol=1e-9)  # fmt: skip


def test_unshaded_ground_fraction_matches_pvlib():
    rot = np.array([20.0, 20.0, -40.0, 0.0])
    phi = np.array([-60.0, 30.0, 10.0, 0.0])
    np.testing.assert_allclose(vf.unshaded_ground_fraction(rot, phi, 0.4), pv._unshaded_ground_fraction(rot, phi, 0.4))


def test_projection_tangent():
    assert vf.solar_projection_tangent(45.0, 180.0, 180.0) == pytest.approx(1.0)
    assert vf.solar_projection_tangent(45.0, 90.0, 180.0) == pytest.approx(0.0, abs=1e-12)


def test_known_values():
    # the whole sky is visible from flat panels; none of it from the underside
    assert vf.vf_row_sky_2d_integ(0.0, 0.4) == pytest.approx(1.0)
    assert vf.vf_row_sky_2d_integ(180.0, 0.4) == pytest.approx(0.0, abs=1e-12)
```

- [ ] **Step 2: Run to verify they fail.** Expected: `ImportError: cannot import name 'viewfactors'`.
- [ ] **Step 3: Port the functions** from the installed pvlib 0.16.1 source, keeping the algorithms unchanged. Module docstring credits pvlib.
- [ ] **Step 4: Run the tests.** Expected: all pass.
- [ ] **Step 5: Commit.** `feat(apv_physics): 2-D view factors ported from pvlib`

---

### Task 6: Panel irradiance and reflection loss

**Files:**
- Create: `apv_physics/src/apv_physics/irradiance.py`, `apv_physics/tests/test_irradiance.py`

**Interfaces:**
- Consumes: `viewfactors` (Task 5)
- Produces:
  - `iam_beam(aoi_deg, a_r: float = 0.16) -> np.ndarray`: port of `pvlib.iam.martin_ruiz`.
  - `iam_diffuse(surface_tilt_deg, a_r: float = 0.16) -> tuple[np.ndarray, np.ndarray]` = `(sky, ground)`: port of `pvlib.iam.martin_ruiz_diffuse` (defaults `c1 = 0.4244`, `c2 = None`).
  - `panel_irradiance(surface_tilt, surface_azimuth, zenith, azimuth, gcr: float, height: float, pitch: float, ghi, dhi, dni, dni_extra, albedo: float) -> dict[str, np.ndarray]` with keys `front_direct, front_sky, front_ground, back_direct, back_sky, back_ground, aoi_front, aoi_back`. A port of `pvlib.bifacial.infinite_sheds.get_irradiance` with `model="haydavies"` and `iam_front = iam_back = 1`: front as given, back at tilt `180 − tilt` and azimuth `+180`. `height` is the row centre height. `surface_tilt` and `surface_azimuth` may be scalars or hourly arrays.
    - When `surface_tilt` is an array (trackers), the three view-factor terms are computed on a 0.5° grid of tilt from 0° to 180° and interpolated linearly, not evaluated per hour.
    - Non-finite intermediate values (sun in the panel plane, sun on the horizon) are replaced by 0 for irradiance and 1 for a shaded fraction.
  - `effective_irradiance(parts: dict, surface_tilt, bifaciality: float, rear_shading: float, a_r: float = 0.16) -> np.ndarray` =
    `fd·iam_beam(aoi_front) + fs·sky(β) + fg·ground(β) + bifaciality·(1 − rear_shading)·[bd·iam_beam(aoi_back) + bs·sky(180 − β) + bg·ground(180 − β)]`

- [ ] **Step 1: Write the failing tests** `apv_physics/tests/test_irradiance.py`

```python
import numpy as np
import pvlib
import pytest
from pvlib.bifacial import infinite_sheds

from apv_physics import load_weather
from apv_physics.irradiance import effective_irradiance, iam_beam, iam_diffuse, panel_irradiance

DATA = __import__("pathlib").Path(__file__).parent / "data"
KEYS = {"front_direct": "poa_front_direct", "front_sky": "poa_front_sky_diffuse",
        "front_ground": "poa_front_ground_diffuse", "back_direct": "poa_back_direct",
        "back_sky": "poa_back_sky_diffuse", "back_ground": "poa_back_ground_diffuse"}  # fmt: skip


def test_iam_beam_values():
    np.testing.assert_allclose(iam_beam(np.array([0.0, 30.0, 60.0, 80.0, 90.0])),
                               [1.0, 0.997466, 0.957912, 0.663481, 0.0], atol=1e-6)  # fmt: skip


def test_iam_diffuse_values():
    sky, ground = iam_diffuse(np.array([20.0, 90.0, 160.0]))
    np.testing.assert_allclose(sky, [0.953406, 0.951460, 0.673630], atol=1e-6)
    np.testing.assert_allclose(ground, [0.673630, 0.951460, 0.953406], atol=1e-6)


def test_single_hour_reference():
    p = panel_irradiance(20.0, 180.0, np.array([40.0]), np.array([150.0]), 0.4, 3.0, 11.4, np.array([700.0]),
                         np.array([150.0]), np.array([720.0]), np.array([1360.0]), 0.2)  # fmt: skip
    expected = {"front_direct": 749.7316, "front_sky": 67.1522, "front_ground": 1.6045, "back_direct": 0.0,
                "back_sky": 1.5298, "back_ground": 71.026}  # fmt: skip
    for k, v in expected.items():
        assert p[k][0] == pytest.approx(v, abs=1e-3), k


@pytest.mark.parametrize("tilt, az, gcr", [(10.0, 180.0, 0.05), (25.0, 135.0, 0.5), (90.0, 90.0, 0.25)])
def test_fixed_matches_pvlib_on_a_real_year(tilt, az, gcr):
    w = load_weather(DATA / "555_ernakulam.npz")
    pitch = 4.56 / gcr
    ours = panel_irradiance(tilt, az, w.zenith, w.azimuth, gcr, 3.0, pitch, w.ghi, w.dhi, w.dni, w.dni_extra, 0.2)
    ref = infinite_sheds.get_irradiance(tilt, az, w.zenith, w.azimuth, gcr, 3.0, pitch, w.ghi, w.dhi, w.dni,
                                        albedo=0.2, model="haydavies", dni_extra=w.dni_extra)  # fmt: skip
    for k, pk in KEYS.items():
        np.testing.assert_allclose(ours[k], np.nan_to_num(ref[pk]), rtol=1e-6, atol=1e-6, err_msg=k)


def test_tracker_interpolation_is_close_to_pvlib():
    w = load_weather(DATA / "107_jodhpur.npz")
    tr = pvlib.tracking.singleaxis(w.zenith, w.azimuth, axis_tilt=0, axis_azimuth=180, max_angle=55, backtrack=True, gcr=0.3)
    tilt, az = np.nan_to_num(tr["surface_tilt"]), np.nan_to_num(tr["surface_azimuth"], nan=90.0)
    ours = panel_irradiance(tilt, az, w.zenith, w.azimuth, 0.3, 2.5, 7.6, w.ghi, w.dhi, w.dni, w.dni_extra, 0.2)
    ref = infinite_sheds.get_irradiance(tilt, az, w.zenith, w.azimuth, 0.3, 2.5, 7.6, w.ghi, w.dhi, w.dni,
                                        albedo=0.2, model="haydavies", dni_extra=w.dni_extra)  # fmt: skip
    for k, pk in KEYS.items():
        assert ours[k].sum() == pytest.approx(np.nansum(ref[pk]), rel=2e-3, abs=1.0), k


def test_no_nan_at_grazing_sun():
    z, a = np.array([89.99, 89.99, 60.0]), np.array([180.0, 90.0, 0.0])  # horizon ahead; in a vertical panel's plane
    one = np.ones(3)
    for tilt, az in ((20.0, 180.0), (90.0, 90.0)):
        p = panel_irradiance(tilt, az, z, a, 0.5, 2.0, 4.0, 50 * one, 40 * one, 300 * one, 1360 * one, 0.2)
        assert all(np.isfinite(v).all() and (v >= 0).all() for k, v in p.items())


def test_effective_irradiance_adds_rear_gain():
    p = panel_irradiance(20.0, 180.0, np.array([40.0]), np.array([150.0]), 0.4, 3.0, 11.4, np.array([700.0]),
                         np.array([150.0]), np.array([720.0]), np.array([1360.0]), 0.2)  # fmt: skip
    mono = effective_irradiance(p, 20.0, 0.0, 0.05)
    bif = effective_irradiance(p, 20.0, 0.8, 0.05)
    assert mono[0] < p["front_direct"][0] + p["front_sky"][0] + p["front_ground"][0]  # reflection loss
    assert bif[0] > mono[0]
```

- [ ] **Step 2: Run to verify they fail.** Expected: `ModuleNotFoundError: apv_physics.irradiance`.
- [ ] **Step 3: Port `iam_beam` and `iam_diffuse`**; run their two tests. Expected: pass.
- [ ] **Step 4: Implement `panel_irradiance`** as a port of `get_irradiance_poa` (Hay–Davies split, `_shaded_fraction`, `_poa_sky_diffuse_pv`, `_poa_ground_shadows`, `_poa_ground_pv`, `beam_component`, `aoi`) called for front and back, with the tracker view-factor grid and the non-finite guards.
- [ ] **Step 5: Implement `effective_irradiance`.**
- [ ] **Step 6: Run the tests.** Expected: all pass.
- [ ] **Step 7: Commit.** `feat(apv_physics): infinite-rows panel irradiance and reflection loss`

---

### Task 7: Temperature and power

**Files:**
- Create: `apv_physics/src/apv_physics/power.py`, `apv_physics/tests/test_power.py`

**Interfaces:**
- Consumes: `Losses` (Task 1)
- Produces:
  - `cell_temperature(g_eff, temp_air, wind_speed) -> np.ndarray` = `temp_air + g_eff / (25.0 + 6.84 × wind_speed)`
  - `dc_power_per_kwp(g_eff, temp_cell, temp_coeff_per_c: float) -> np.ndarray`: W per kWp before losses = `g_eff × (1 + temp_coeff × (temp_cell − 25))`, floored at 0
  - `ac_power_per_kwp(p_dc, losses: Losses) -> np.ndarray`: `p = p_dc × losses.dc_factor`; PVWatts inverter with `pac0 = 1000 / dc_ac_ratio`, `pdc0 = pac0 / inverter_efficiency`, `ζ = p / pdc0`, `η = inverter_efficiency / 0.9637 × (−0.0162 ζ − 0.0059 / ζ + 0.9858)`, AC = `min(η × p, pac0)`, 0 where `p == 0`, floored at 0; then `× losses.ac_factor`

- [ ] **Step 1: Write the failing tests** `apv_physics/tests/test_power.py`

```python
import numpy as np
import pvlib
import pytest

from apv_physics import Losses
from apv_physics.power import ac_power_per_kwp, cell_temperature, dc_power_per_kwp

NO_LOSS = Losses(soiling=0.0, mismatch=0.0, dc_wiring=0.0, connections=0.0, ac_wiring=0.0)


def test_cell_temperature():
    assert cell_temperature(np.array([800.0]), np.array([20.0]), np.array([1.0]))[0] == pytest.approx(45.125628)


def test_dc_power():
    assert dc_power_per_kwp(np.array([1000.0]), np.array([25.0]), -0.003)[0] == pytest.approx(1000.0)
    assert dc_power_per_kwp(np.array([800.0]), np.array([45.0]), -0.003)[0] == pytest.approx(752.0)
    assert dc_power_per_kwp(np.array([100.0]), np.array([400.0]), -0.005)[0] == 0.0


def test_inverter_without_other_losses():
    out = ac_power_per_kwp(np.array([500.0, 100.0, 1000.0, 0.0]), NO_LOSS)
    np.testing.assert_allclose(out, [491.293945, 95.147784, 800.0, 0.0], atol=1e-5)


def test_default_losses_match_pvlib():
    p = np.linspace(0.0, 1100.0, 56)
    L = Losses()
    ref = pvlib.inverter.pvwatts(p * L.dc_factor, 800.0 / 0.98, eta_inv_nom=0.98) * L.ac_factor
    np.testing.assert_allclose(ac_power_per_kwp(p, L), ref, atol=1e-9)
    assert ac_power_per_kwp(p, L).max() == pytest.approx(800.0 * 0.985)
```

- [ ] **Step 2: Run to verify they fail.** Expected: `ModuleNotFoundError: apv_physics.power`.
- [ ] **Step 3: Implement the three functions.**
- [ ] **Step 4: Run the tests.** Expected: all pass.
- [ ] **Step 5: Commit.** `feat(apv_physics): cell temperature, DC and AC power`

---

### Task 8: Ground light

**Files:**
- Create: `apv_physics/src/apv_physics/ground.py`, `apv_physics/tests/test_ground.py`

**Interfaces:**
- Consumes: `viewfactors.vf_ground_sky_2d`, `viewfactors.solar_projection_tangent` (Task 5); `Weather` (Task 1)
- Geometry (pvlib's convention): a horizontal axis `x` across the rows, pointing **away from** `ref_azimuth_deg`. Row `k` is centred at `x = k × pitch`, height `h`. Its edges are `(k·pitch ± ½·w·cos θ, h ± ½·w·sin θ)` for signed rotation `θ` (positive = panel faces `ref_azimuth_deg`). A point at `(x, z)` casts its shadow at `x + z × tan φ`, with `tan φ = solar_projection_tangent(zenith, azimuth, ref_azimuth_deg)`. Strip `j` covers `[j, j + 1) × pitch / 100`.
- Produces:
  - `N_STRIPS = 100`
  - `strip_unshaded(rotation, tan_phi, gcr: float, height: float, pitch: float) -> np.ndarray`, shape `(n_hours, 100)`: the share of each strip in direct sun. The shadow of row 0 is the interval between its two edge shadows; its length is capped at `pitch`; it repeats every `pitch`. Each strip's value is `1 − (overlap of the shadow with the strip, wrapped around the pitch) / strip width`. This is exact, so the mean over strips is `1 − min(1, shadow length / pitch)`.
  - `strip_sky_view(rotation, gcr: float, height: float, pitch: float) -> np.ndarray`: `vf_ground_sky_2d` at strip centres `x = (j + 0.5) / 100` with `max_rows = ceil(height / (pitch × tan 5°))`. Scalar `rotation` → shape `(100,)`. Array `rotation` → shape `(n_hours, 100)`, computed on a 0.5° grid over the range of `rotation` and looked up by nearest grid angle.
  - `farmed_mask(pitch: float, unfarmed_strip_m: float) -> np.ndarray` (bool, 100): True where the strip centre is farther than `unfarmed_strip_m / 2` from the nearest row centre. All True when `unfarmed_strip_m == 0`. Raises `ValueError("unfarmed_strip_m leaves no farmed ground ...")` when nothing is True.
  - `ground_light(weather: Weather, rotation, ref_azimuth_deg: float, gcr: float, height: float, collector_width_m: float, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]` = `(light_mean, light_darkest_tenth)`, each shape `(12,)`, within `[0, 1]`:
    - `AI = clip(dni / dni_extra, 0, 1)`; `beam = dni × max(cos Z, 0) + dhi × AI`; `iso = dhi × (1 − AI)`
    - strip light per hour = `beam × strip_unshaded + iso × strip_sky_view`
    - per month `m`: `S[m, j]` = sum over that month's hours; `D[m]` = sum of `beam + iso`
    - `light_mean[m] = mean(S[m, mask]) / D[m]`
    - `light_darkest_tenth[m]` = mean of the lowest `ceil(0.1 × mask.sum())` values of `S[m, mask]`, divided by `D[m]`
    - a month with `D[m] == 0` gives 1.0 for both

  The denominator is open-field light under the same split (`beam + iso`). It equals GHI up to the pack's rounding. With almost no panels the result is within 0.002 of 1, not exactly 1, because the ported sky view leaves out the sky within about 5° of the horizon (`max_rows`). The GCR 0 row is set to exactly 1 in `simulate`.

- [ ] **Step 1: Write the failing tests** `apv_physics/tests/test_ground.py`

```python
import numpy as np
import pytest
from pvlib.bifacial import utils as pv
from helpers import weather

from apv_physics import load_weather
from apv_physics.ground import N_STRIPS, farmed_mask, ground_light, strip_sky_view, strip_unshaded

DATA = __import__("pathlib").Path(__file__).parent / "data"
ALL = np.ones(N_STRIPS, dtype=bool)


def test_overhead_sun_flat_panels_shade_equals_density():
    u = strip_unshaded(np.array([0.0]), np.array([0.0]), 0.30, 3.0, 10.0)
    assert u.shape == (1, 100)
    assert (u[0] < 1e-9).sum() == 30 and (u[0] > 1 - 1e-9).sum() == 70
    np.testing.assert_allclose(u[0, :15], 0.0, atol=1e-9)  # the shadow is centred under the row
    np.testing.assert_allclose(u[0, -15:], 0.0, atol=1e-9)


def test_partly_shaded_strip_is_fractional():
    u = strip_unshaded(np.array([0.0]), np.array([0.0]), 0.25, 3.0, 10.0)  # shadow edge at 1.25 m, mid-strip
    assert u[0, 12] == pytest.approx(0.5) and u[0].mean() == pytest.approx(0.75)


def test_shadow_moves_with_the_sun():
    # flat row at 3 m, tan(phi) = 1: the shadow shifts 3 m along +x
    u = strip_unshaded(np.array([0.0]), np.array([1.0]), 0.20, 3.0, 10.0)
    np.testing.assert_allclose(u[0, 20:40], 0.0, atol=1e-9)
    assert u[0].mean() == pytest.approx(0.8)


def test_tilted_row_shadow_length():
    # width 4, tilt 30 deg, tan(phi) = 1: edges at x = +-1.732, z = 3 +- 1 -> shadows at 5.732 and 0.268
    u = strip_unshaded(np.array([30.0]), np.array([1.0]), 0.4, 3.0, 10.0)
    assert u[0].mean() == pytest.approx(1 - 5.4641 / 10.0, abs=1e-4)


@pytest.mark.parametrize("height", [0.75, 2.5, 6.0])
def test_mean_matches_energy_balance_for_any_height(height):
    rot, tan_phi = np.array([20.0, 20.0, -35.0]), np.array([-2.5, 0.7, 8.0])
    u = strip_unshaded(rot, tan_phi, 0.4, height, 11.4)
    w = 0.4 * 11.4
    length = np.minimum(np.abs(w * np.cos(np.radians(rot)) + w * np.sin(np.radians(rot)) * tan_phi), 11.4)
    np.testing.assert_allclose(u.mean(axis=1), 1 - length / 11.4, atol=1e-9)


def test_grazing_sun_is_finite():
    u = strip_unshaded(np.array([20.0, 90.0]), np.array([5e3, -5e3]), 0.5, 2.0, 4.0)
    assert np.isfinite(u).all() and (u >= 0).all() and (u <= 1).all()


def test_sky_view_matches_pvlib_and_shapes():
    v = strip_sky_view(20.0, 0.4, 3.0, 11.4)
    x = (np.arange(100) + 0.5) / 100
    ref = pv.vf_ground_sky_2d(20.0, 0.4, x, 11.4, 3.0, max_rows=np.ceil(3.0 / (11.4 * np.tan(np.radians(5)))))
    np.testing.assert_allclose(v, np.ravel(ref), rtol=1e-9)
    rot = np.array([-50.0, 0.3, 12.2, 55.0])
    assert strip_sky_view(rot, 0.4, 2.5, 5.7).shape == (4, 100)


def test_farmed_mask():
    assert farmed_mask(10.0, 0.0).all()
    m = farmed_mask(10.0, 1.0)  # 0.5 m either side of the row centre
    assert (~m).sum() == 10 and not m[:5].any() and not m[-5:].any() and m[5:95].all()


def test_no_farmed_ground_raises():
    with pytest.raises(ValueError, match="^unfarmed_strip_m"):
        farmed_mask(1.0, 3.0)


def test_open_sky_gives_one():
    w = weather(n=4, month=np.array([1, 1, 7, 7]))
    mean, dark = ground_light(w, 0.0, 180.0, 1e-6, 3.0, 1e-5, ALL)
    # not exactly 1: the ported sky view leaves out the sky within about 5 degrees of the horizon
    assert mean[0] == pytest.approx(1.0, abs=2e-3) and mean[6] == pytest.approx(1.0, abs=2e-3)
    assert mean[3] == 1.0 and dark[3] == 1.0  # a month with no hours


def test_real_year_ranges_and_evenness():
    w = load_weather(DATA / "107_jodhpur.npz")
    low_mean, low_dark = ground_light(w, 20.0, 180.0, 0.4, 2.5 + 0.78, 4.56, ALL)
    high_mean, high_dark = ground_light(w, 20.0, 180.0, 0.4, 6.0 + 0.78, 4.56, ALL)
    assert ((0 < low_mean) & (low_mean < 1)).all() and (low_dark <= low_mean + 1e-12).all()
    np.testing.assert_allclose(low_mean, high_mean, atol=0.005)  # height does not change the mean
    assert high_dark.mean() > low_dark.mean()  # taller rows give more even light


def test_mean_close_to_pvlib_reference():
    w = load_weather(DATA / "555_ernakulam.npz")
    gcr, tilt, pitch, h = 0.25, 15.0, 4.56 / 0.25, 3.0
    mean, _ = ground_light(w, tilt, 180.0, gcr, h, 4.56, ALL)
    ai = np.clip(w.dni / w.dni_extra, 0, 1)
    beam, iso = w.dni * np.clip(np.cos(np.radians(w.zenith)), 0, None) + w.dhi * ai, w.dhi * (1 - ai)
    phi = np.degrees(np.arctan(pv._solar_projection_tangent(w.zenith, w.azimuth, 180.0)))
    f = pv._unshaded_ground_fraction(tilt, phi, gcr, max_zenith=90)
    v = pv.vf_ground_sky_2d_integ(tilt, gcr, h, pitch)
    assert mean.mean() == pytest.approx(((beam * f).sum() + iso.sum() * v) / (beam + iso).sum(), abs=0.01)
```

- [ ] **Step 2: Run to verify they fail.** Expected: `ModuleNotFoundError: apv_physics.ground`.
- [ ] **Step 3: Implement `strip_unshaded`** with array operations only (no loop over hours). Run its six tests. Expected: pass.
- [ ] **Step 4: Implement `strip_sky_view` and `farmed_mask`.** Run their tests. Expected: pass.
- [ ] **Step 5: Implement `ground_light`.** Run the whole file. Expected: all pass.
- [ ] **Step 6: Commit.** `feat(apv_physics): strip-by-strip ground light and evenness`

---

### Task 9: `simulate()`, properties, pvlib agreement, speed, snapshots

**Files:**
- Create: `apv_physics/src/apv_physics/simulate.py`, `apv_physics/README.md`, `apv_physics/tests/reference.py`, `apv_physics/tests/test_simulate.py`, `apv_physics/tests/test_properties.py`, `apv_physics/tests/test_against_pvlib.py`, `apv_physics/tests/test_snapshots.py`, `apv_physics/tests/data/snapshots/*.csv`
- Modify: `apv_physics/src/apv_physics/__init__.py` (export `PhysicsResult`, `simulate`, `reference_energy_kwh_per_acre`)

**Interfaces:**
- Consumes: everything from Tasks 1–8; `apv_core.physics.PhysicsTable`, `apv_core.physics.kwp_per_acre`, `apv_core.constants.GCR_GRID`
- Produces:
  - `@dataclass(frozen=True) class PhysicsResult(table: PhysicsTable, light_darkest_tenth: np.ndarray, clear_gap_m: np.ndarray)`: shapes 11 × 12 and 11; `light_darkest_tenth[0]` is all 1.0; `clear_gap_m[0]` is `inf`
  - `simulate(weather: Weather, layout: Layout, losses: Losses = Losses()) -> PhysicsResult`. For each GCR above 0, with `pitch = collector_width_m / gcr`:

    | | fixed | vertical | tracker |
    |---|---|---|---|
    | rotation `θ` | `tilt_deg` | 90 | `tracker_rotation(...)` (hourly) |
    | `ref_azimuth_deg` | `azimuth_deg` | `azimuth_deg` | 270 |
    | surface tilt, azimuth | `tilt_deg`, `azimuth_deg` | 90, `azimuth_deg` | `|θ|`, 270 where `θ ≥ 0` else 90 |
    | farmed strip | all | `farmed_mask(pitch, unfarmed_strip_m)` | all |
    | `clear_gap_m` | `pitch − w·cos(tilt)` | `pitch` | `pitch − w` |

    Energy: `panel_irradiance` (height = `layout.center_height_m`, albedo = `losses.albedo`) → `effective_irradiance` → `cell_temperature` → `dc_power_per_kwp` → `ac_power_per_kwp`; monthly sum ÷ 1000 gives kWh per kWp. Light: `ground_light`.
  - `reference_energy_kwh_per_acre(weather: Weather, module: Module, losses: Losses = Losses()) -> float`: fixed, azimuth 180, tilt `clip(weather.optimum_tilt_deg, 10, 25)`, GCR 0.45, collector width 4.56, centre height 1.5; annual kWh/kWp × `kwp_per_acre(0.45, module.efficiency)`. `simulate` stores it in `table.ref_energy_kwh_per_acre`.
  - `tests/reference.py`: `pvlib_reference(weather, layout, gcr, losses) -> tuple[np.ndarray, float]` = (monthly kWh/kWp, annual mean ground light), built only from pvlib calls: `tracking.singleaxis`, `infinite_sheds.get_irradiance` (with `iam_front`/`iam_back` from `pvlib.iam.martin_ruiz`), `iam.martin_ruiz_diffuse` on the sky and ground parts, `temperature.faiman`, `pvsystem.pvwatts_dc`, `inverter.pvwatts`, and for light `_unshaded_ground_fraction(..., max_zenith=90)` with `vf_ground_sky_2d_integ`.

- [ ] **Step 1: Write the failing tests** `apv_physics/tests/test_simulate.py`

```python
import time

import numpy as np
import pytest
from helpers import weather

from apv_core.constants import GCR_GRID
from apv_core.physics import kwp_per_acre
from apv_physics import BIFACIAL, MONOFACIAL, Kind, Layout, load_weather, reference_energy_kwh_per_acre, simulate

DATA = __import__("pathlib").Path(__file__).parent / "data"
JODHPUR = load_weather(DATA / "107_jodhpur.npz")
FIXED = Layout(Kind.FIXED, BIFACIAL, height_m=3.0, collector_width_m=4.56, tilt_deg=20.0)
TRACKER = Layout(Kind.TRACKER, BIFACIAL, height_m=2.5, collector_width_m=2.28)
VERTICAL = Layout(Kind.VERTICAL, BIFACIAL, height_m=0.8, collector_width_m=2.27, azimuth_deg=90.0)


@pytest.mark.parametrize("layout", [FIXED, TRACKER, VERTICAL])
def test_shapes_and_open_field_row(layout):
    r = simulate(JODHPUR, layout)
    assert r.table.energy_kwh_per_kwp.shape == (11, 12) and r.light_darkest_tenth.shape == (11, 12)
    assert (r.table.energy_kwh_per_kwp[0] == 0).all() and (r.table.light_fraction[0] == 1).all()
    assert (r.light_darkest_tenth[0] == 1).all() and np.isinf(r.clear_gap_m[0])
    assert np.isfinite(r.table.energy_kwh_per_kwp).all()


def test_jodhpur_fixed_is_plausible():
    r = simulate(JODHPUR, Layout(Kind.FIXED, MONOFACIAL, 3.0, 4.56, tilt_deg=25.0))
    annual = r.table.energy_kwh_per_kwp.sum(axis=1)
    assert 1600 < annual[1] < 1950  # Global Solar Atlas gives 1,752 at the optimum tilt
    light = r.table.light_fraction.mean(axis=1)
    assert 0.65 < light[5] < 0.80 and 0.45 < light[9] < 0.60  # GCR 0.25 and 0.45


def test_tracker_beats_fixed_and_vertical_trails():
    e = {k: simulate(JODHPUR, l).table.energy_kwh_per_kwp[5].sum() for k, l in
         {"fixed": FIXED, "tracker": TRACKER, "vertical": VERTICAL}.items()}  # fmt: skip
    assert e["tracker"] > e["fixed"] > e["vertical"]


def test_clear_gap():
    r = simulate(JODHPUR, FIXED)
    assert r.clear_gap_m[5] == pytest.approx(4.56 / 0.25 - 4.56 * np.cos(np.radians(20.0)))
    assert simulate(JODHPUR, TRACKER).clear_gap_m[10] == pytest.approx(2.28 / 0.5 - 2.28)


def test_reference_plant():
    ref = reference_energy_kwh_per_acre(JODHPUR, BIFACIAL)
    assert simulate(JODHPUR, FIXED).table.ref_energy_kwh_per_acre == pytest.approx(ref)
    assert 1500 * kwp_per_acre(0.45, 0.225) < ref < 2100 * kwp_per_acre(0.45, 0.225)


def test_missing_month_is_safe():
    r = simulate(weather(n=6, month=np.array([1, 1, 1, 7, 7, 7])), FIXED)
    assert (r.table.energy_kwh_per_kwp[:, 3] == 0).all() and (r.table.light_fraction[:, 3] == 1).all()


@pytest.mark.parametrize("layout", [
    Layout(Kind.FIXED, BIFACIAL, 6.0, 0.5, tilt_deg=20.0),
    Layout(Kind.FIXED, BIFACIAL, 0.5, 10.0, tilt_deg=20.0),
    Layout(Kind.FIXED, MONOFACIAL, 2.0, 4.56, tilt_deg=0.0),
    Layout(Kind.FIXED, BIFACIAL, 3.0, 4.56, tilt_deg=40.0, azimuth_deg=90.0),
    Layout(Kind.TRACKER, BIFACIAL, 6.0, 0.5, max_angle_deg=60.0),
])  # fmt: skip
def test_limit_corners(layout):
    r = simulate(JODHPUR, layout)
    assert np.isfinite(r.table.energy_kwh_per_kwp).all()
    assert ((r.table.light_fraction >= 0) & (r.table.light_fraction <= 1)).all()


@pytest.mark.parametrize("layout", [FIXED, TRACKER, VERTICAL])
def test_speed(layout):
    simulate(JODHPUR, layout)  # warm-up
    t = time.perf_counter()
    simulate(JODHPUR, layout)
    assert time.perf_counter() - t < 2.0


def test_no_heavy_imports():
    import subprocess
    import sys

    code = "import sys, apv_physics; print(any(m in sys.modules for m in ('pandas', 'scipy', 'pvlib')))"
    assert subprocess.run([sys.executable, "-c", code], capture_output=True, text=True).stdout.strip() == "False"
```

- [ ] **Step 2: Run to verify they fail.** Expected: `ImportError: cannot import name 'simulate'`.
- [ ] **Step 3: Implement `simulate.py`** to the Interfaces block. Run `test_simulate.py`. Expected: all pass. Print the three timings; if any exceeds 0.6 s, profile and fix before continuing (spec §5.5).
- [ ] **Step 4: Write the property tests** `apv_physics/tests/test_properties.py` (Hypothesis, `max_examples=25`, `deadline=None`), using the Ernakulam pack and a strategy that draws valid fixed, tracker and vertical layouts within the limits:
  - `test_light_never_rises_with_gcr`: for each month, `light_fraction[i + 1] <= light_fraction[i] + 1e-9`.
  - `test_mean_light_ignores_height_and_width`: two fixed layouts differing only in `height_m` and `collector_width_m` have `light_fraction` equal within 0.005.
  - `test_darkest_tenth_not_above_mean`: `light_darkest_tenth <= light_fraction + 1e-9`.
  - `test_fixed_energy_never_rises_with_gcr`: annual kWh/kWp for rows 1..10 is non-increasing within 1e-6 (fixed layouts only).
  - `test_outputs_finite_and_in_range`: energy finite and ≥ 0; light within [0, 1].
- [ ] **Step 5: Run the property tests.** Expected: pass. A failure here is a finding about the engine; fix the engine, not the test.
- [ ] **Step 6: Write `tests/reference.py` and `tests/test_against_pvlib.py`** (spec §7, V1). Parametrise over the three sample packs × these layouts × GCR 0.05, 0.25, 0.50: fixed tilt 10 and 25 at azimuth 180 and 135, each with `MONOFACIAL` and `BIFACIAL`; tracker at max angle 45 and 55 (bifacial); vertical at azimuth 90 (bifacial). Assert: annual energy within ±1 %; each month within ±2 %; annual mean ground light within ±0.01. Mark the module `pytest.mark.slow` only if it runs longer than 60 s.
- [ ] **Step 7: Run them.** Expected: pass. If a case fails, report the district, layout, GCR and both numbers; find the cause in the engine or the reference chain. Do not widen the tolerance.
- [ ] **Step 8: Create snapshots.** `tests/test_snapshots.py` compares `simulate` output (monthly energy, light, darkest tenth for GCR 0.25) for Jodhpur fixed, Ernakulam tracker and Leh vertical against `tests/data/snapshots/<name>.csv` with `rtol=1e-6`; a helper run with `APV_PHYSICS_WRITE_SNAPSHOTS=1` writes the files. Generate them once, read them for sanity, commit.
- [ ] **Step 9: Write `apv_physics/README.md`**: what it computes, a 15-line usage example (`load_weather` → `Layout` → `simulate` → `run_sweep`), the inputs and limits table, what height and row width do and do not change, what is left out, how to run the tests, and the pvlib credit.
- [ ] **Step 10: Run the full suite and lint.** `pytest apv_physics -q` and `ruff check apv_physics`. Expected: all pass, no warnings. Also run `pytest apv_core -q`. Expected: 82 passed.
- [ ] **Step 11: Commit.** `feat(apv_physics): simulate() with pvlib agreement, property and speed tests`

---

### Task 10: Validate against Global Solar Atlas and PySAM

**Files:**
- Create: `pipeline/src/pipeline/validation/__init__.py`, `pipeline/src/pipeline/validation/physics_validation.py`, `data/validation/physics_validation.csv` (output)
- Modify: `docs/superpowers/specs/2026-11-14-live-physics-design.md` (record results under §7), `research/README.md` (one line under D18 pointing to the results)

**Interfaces:**
- Consumes: `simulate`, `load_weather`, `Layout`, `MONOFACIAL`, `Losses`; `data/weather/` packs and `index.json` (Task 3); `research/10_validation/energy_reference/energy_reference.csv` (rows with `kind == "district_reference"`: `ref_id, dist_lgd, district, gsa_pvout_kwh_per_kwp_yr, gsa_opt_tilt_deg`; rows with `kind == "measured_plant"` are copied for information); calibrated hourly CSVs (full 8,760 hours, for PySAM)
- Produces:
  - `engine_annual(pack_path, tilt_deg) -> float`: `simulate` with `Layout(Kind.FIXED, MONOFACIAL, height_m=1.0, collector_width_m=2.278, tilt_deg=tilt_deg, azimuth_deg=180.0)`; annual kWh/kWp at GCR 0.05 (row 1)
  - `pysam_annual(csv_path, lat, lon, elevation_m, tilt_deg, losses) -> float`: `PySAM.Pvwattsv8` with `solar_resource_data` built from the calibrated file (`year, month, day, hour, minute = 0`, `dn, df, gh, tdry, wspd`, `tz = 0`, `lat, lon, elev`), `system_capacity = 1000`, `module_type = 0`, `array_type = 0`, `tilt`, `azimuth = 180`, `gcr = 0.05`, `dc_ac_ratio = 1.25`, `inv_eff = 98`, `bifaciality = 0`, `losses = 100 × (1 − dc_factor × ac_factor)`; returns `ac_annual / 1000`
  - CLI `python -m pipeline.validation.physics_validation <repo_root>`: writes `data/validation/physics_validation.csv` with columns `ref_id, kind, district, tilt_deg, engine_kwh_per_kwp, gsa_pvout_kwh_per_kwp, engine_vs_gsa_pct, pysam_kwh_per_kwp, engine_vs_pysam_pct, pass_gsa, pass_pysam, note`; prints the table; exits 1 if any reference district is outside ±7 % of the Atlas or ±3 % of PySAM

- [ ] **Step 1: Implement `engine_annual` and the Atlas comparison.** Run the CLI with PySAM columns left blank. Expected: 10 rows; Jodhpur near 1,796 kWh/kWp, about 2.5 % above the Atlas's 1,752 (a pvlib prototype of the same chain gave this on 2026-11-14).
- [ ] **Step 2: Implement `pysam_annual`.** Before trusting its energy, check its plane-of-array total for Jodhpur against the engine's front irradiance total; they should agree within 2 %. A larger gap means the time convention (`tz`, `minute`) is wrong; fix that first.
- [ ] **Step 3: Run the full validation.** Run: `uv run --no-project --with-editable ./apv_core --with-editable ./apv_physics --with-editable "./pipeline[validation]" python -m pipeline.validation.physics_validation .`
- [ ] **Step 4: Report honestly.** If every district passes, record the table in the spec (§7) with the date. If any fails, do not change the losses or tolerances: record the failing rows, say which check failed and by how much, state the likely cause (for PySAM, its Perez sky model against our Hay–Davies), and stop for the owner's decision (spec §7, §9).
- [ ] **Step 5: Commit.** `feat(pipeline): validate the physics engine against Global Solar Atlas and PySAM`
