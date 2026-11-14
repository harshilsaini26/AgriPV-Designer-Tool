# apv_physics

The live physics engine of **AgriPV Lab**. Given one district's hourly weather and a panel layout, it works
out, for every panel density (GCR 0.00–0.50):

- the **energy** the panels produce each month, per kWp;
- the **light** that reaches the crop each month, as a share of open-field light;
- how **even** that light is: the light on the darkest tenth of the farmed ground;
- the **clear gap** between rows, for machinery.

It needs numpy and `apv_core` only, so it is small enough to run inside the API function. pvlib and PySAM are
used in tests and offline validation, never at runtime. Design:
[`docs/superpowers/specs/2026-11-14-live-physics-design.md`](../docs/superpowers/specs/2026-11-14-live-physics-design.md).

## Use

```python
from apv_core import BusinessModel, Structure, SweepInputs, run_sweep
from apv_physics import BIFACIAL, Kind, Layout, load_weather, simulate

weather = load_weather("data/weather/107_jodhpur.npz")  # built by pipeline.weather.build_packs
layout = Layout(Kind.FIXED, BIFACIAL, height_m=3.0, collector_width_m=4.56, tilt_deg=25.0, azimuth_deg=180.0)

result = simulate(weather, layout)
result.table.energy_kwh_per_kwp  # 11 x 12: density x month; row 0 is the open field
result.table.light_fraction  # 11 x 12: average light on the farmed ground
result.light_darkest_tenth  # 11 x 12: light on the darkest tenth of the farmed ground
result.clear_gap_m  # 11: open ground between adjacent rows

structure = Structure("custom", a_farm=0.92, module_efficiency=layout.module.efficiency)
sweep = run_sweep(
    SweepInputs(
        physics=result.table,
        structure=structure,
        rotation=...,
        finance=...,
        business_model=BusinessModel.KUSUM_A,
    )
)
```

## Inputs and limits

| Field | Applies to | Limits | Meaning |
|---|---|---|---|
| `kind` | all | `fixed`, `tracker`, `vertical` | Structure type |
| `tilt_deg` | fixed | 0–40 | Panel tilt from horizontal |
| `azimuth_deg` | fixed, vertical | 90–270 | Direction the front faces (180 = south) |
| `max_angle_deg` | tracker | 30–60 | Turning limit either side of flat; the axis runs north–south and backtracking is on |
| `height_m` | all | 0.5–6.0 | Fixed and vertical: lower panel edge above the ground. Tracker: axis height |
| `collector_width_m` | all | 0.5–10.0 | Panel surface width across the row |
| `unfarmed_strip_m` | vertical | 0–3.0 | Strip under each row that is not cropped |
| `module.efficiency` | all | 0.15–0.25 | Presets: `BIFACIAL` 0.225, `MONOFACIAL` 0.210 |
| `module.bifaciality` | all | 0–0.95 | Share of rear-side light the cells can use |
| `module.temp_coeff_per_c` | all | −0.005 to −0.002 | Power change per °C of cell temperature |

A value outside its limits raises `ValueError`, and the message starts with the field name.

## What height and row width do

The model treats the rows as repeating without end. In that geometry the **average** light on the ground and
the energy per kWp depend only on density, tilt and direction. Panel height and row width do not change
them. They change **where** the shade falls: taller or narrower rows spread it more evenly. So `height_m` and
`collector_width_m` move `light_darkest_tenth` and `clear_gap_m`, not `light_fraction` or energy.

## What the model leaves out

- Light reflected off panels or passing through gaps between modules, and extra light at the edges of a small
  plant. Both mean the model slightly understates light on the crop.
- Posts and tracks: covered by the farmable fraction `a_farm` in `apv_core`.
- Plant downtime and panel degradation: finance inputs in `apv_core`, not applied here.
- With an unfarmed strip under vertical rows, light on the farmed band can rise slightly between two
  densities (0.005 seen in one month), because row shadows land on the unfarmed strip. Light over the whole
  ground never rises with density.

## Losses

Fixed in `Losses`: soiling 4%, mismatch 1%, DC wiring 1.5%, connections 0.5%, AC wiring 1.5%, inverter 98%
with a DC/AC ratio of 1.25, rear-side shading 5%, ground albedo 0.20. They are assumptions written down
before any comparison with reference data, and are not tuned.

## Tests

```bash
uv run --no-project --with-editable ./apv_core --with-editable "./apv_physics[dev]" python -m pytest apv_physics -q
```

- **Known answers:** hand geometry for shadows, tracker angles, temperature and inverter values.
- **Against pvlib** (`tests/test_against_pvlib.py`): 11 layouts × 3 sample districts × 3 densities. Annual
  energy must be within 1%, each month within 2% and ground light within 0.01. Measured: energy agrees to
  better than 0.001%, ground light within 0.001.
- **Properties** (`tests/test_properties.py`): random valid layouts; outputs finite and in range, whole-ground
  light never rises with density, mean light independent of height and width.
- **Speed:** each layout must finish in under 2 s. Measured on a laptop: 0.25–0.41 s for the presets, 0.67 s
  for the most extreme allowed layout.
- **Snapshots** (`tests/data/snapshots/`): monthly results for three district-and-layout pairs.

## Credits

`viewfactors.py` and `irradiance.py` are adapted from [pvlib-python](https://github.com/pvlib/pvlib-python)
0.16.1 (BSD 3-Clause); see [`NOTICE`](NOTICE). The sample weather packs in `tests/data/` derive from PVGIS
© European Union (JRC), PVGIS-ERA5 2005–2023, containing modified Copernicus Climate Change Service
information, calibrated to the Global Solar Atlas 2.0 (Solargis / World Bank Group, CC BY 4.0).
