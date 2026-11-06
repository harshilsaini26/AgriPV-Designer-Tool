# research/

All raw data, literature and research notes for AgriPV Lab live here. **Start with
[`DATA_REQUIREMENTS.md`](DATA_REQUIREMENTS.md)**: it lists every dataset (D00 to D25), why it is needed, the exact
fields to collect, and when it counts as done.

| Folder | Datasets |
|---|---|
| `00_admin_boundaries/` | D00: district list, LGD codes, boundaries, mapping |
| `01_agro_climate/` (`zones/`, `rainfall/`, `temperature/`) | D01 to D03 |
| `02_soil/` | D04 |
| `03_elevation/` | D05 |
| `04_land_cover/` | D06: cropland mask |
| `05_groundwater_irrigation/` (`cgwb_assessment/`, `irrigation_and_pumps/`, `landholdings/`) | D07 to D09 |
| `06_crops/` (`area_production_yield/`, `crop_calendar/`) | D10, D11 |
| `07_crop_economics/` (`cost_of_cultivation/`, `prices/`) | D12, D13 |
| `08_solar_weather/` (`tmy/`, `solar_atlas/`, `albedo/`) | D14, D15 |
| `09_crop_shade_response/` (`papers/`, `extraction/`, `parameters/`) | D16: the riskiest research |
| `10_validation/` (`field_trials/`, `energy_reference/`) | D17, D18 |
| `11_finance_policy/` (`kusum/`, `capex_om/`, `lending_tax/`, `land_lease/`, `yield_limit_policy/`) | D19 to D23 |
| `12_structures_technology/` | D24 |
| `13_stakeholder_notes/` | D25 |
| `_templates/` | `SOURCE.md` provenance card |

## Rules
1. Every source gets a `SOURCE.md` (copy from `_templates/`) **before** you process it.
2. Large downloads go in the folder's `raw/`, which is git-ignored. Small CSVs and notes are committed.
3. Join on **LGD codes**, never on district names.
4. Paper PDFs stay local (git-ignored). Commit citations and extracted numbers only.
5. No personal data anywhere in the repo.
