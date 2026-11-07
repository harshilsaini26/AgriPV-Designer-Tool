# SOURCE: CGWB groundwater levels (manual quarterly well readings) via NWIC National Water Data Portal: district depth 2021–2025

| Field | Value |
|---|---|
| Dataset ID | D07 (depth to water; complements the CGWB stage-of-extraction tables) |
| Publisher / owner | Central Ground Water Board (CGWB) readings, published by the National Water Informatics Centre (NWIC), Department of Water Resources, RD & GR, Ministry of Jal Shakti |
| Dataset name and version | "Ground Water Level (Manual - Quarterly), Central Ground Water Board" (CKAN id `gwl-manual-quarterly-central-ground-water-board-department`; 95 state files, 1991–2020 and 2021–2025; metadata modified 2026-11-07). The 31 files for **2021–2025** are used |
| URL / access route | https://nwdp.nwic.gov.in/dataset/gwl-manual-quarterly-central-ground-water-board-department (file list via `https://nwdp.nwic.gov.in/api/3/action/package_show?id=gwl-manual-quarterly-central-ground-water-board-department`) |
| Accessed on (YYYY-MM-DD) | 2026-11-07 |
| Reference year(s) covered | 2021–2025 |
| Spatial coverage | All states with CGWB monitoring wells: 552 districts with data; 402 with enough pre-monsoon readings |
| Spatial unit or resolution | Well points (lat / lon, with **LGD state and district codes in every record**), aggregated to districts |
| Temporal resolution | Quarterly campaigns (January, pre-monsoon May / June, August, post-monsoon November) |
| Licence | Portal licence tag "Other (Open)". NWIC copyright policy: "Material featured on this site may be reproduced free of charge in any format or media without requiring specific permission", provided it is reproduced accurately and the source is prominently acknowledged (checked 2026-11-07) |
| OK for a public open-source app? | **OK** with attribution |
| Required attribution text | "Groundwater levels: Central Ground Water Board, via National Water Informatics Centre (NWIC), Ministry of Jal Shakti, National Water Data Portal (nwdp.nwic.gov.in)" |
| Citation | CGWB / NWIC (2026). Ground Water Level (Manual – Quarterly), Central Ground Water Board. National Water Data Portal |
| Files in this folder | Committed: `nwic_gwl_district_depth_2021-2025.csv` (552 rows). Git-ignored: `raw/nwic_gwl/gwl_manual_quarterly_cgwb_<state>_2021_2025.csv` (31 files, ≈ 23 MB) |
| Units and key column meanings | `dist_lgd` (from the source records), `district`, `state_lgd`, `state`, `n_wells_pre` / `n_wells_post` (wells with ≥ 2 readings in that season), `pre_monsoon_depth_m` / `post_monsoon_depth_m` (median depth to water, **metres below ground level**), `seasonal_rise_m` (pre − post; positive = monsoon recharge), `pre_monsoon_band` (CGWB / ICED depth classes: 0–2, 2–5, 5–10, 10–20, 20–40, > 40 m) |
| Known caveats and gaps | (1) **These are mostly dug wells and piezometers in the shallow (phreatic) aquifer, not irrigation borewells**: hard-rock districts can look shallow (Kolar 3 m) even where farmers' borewells go hundreds of metres deep, so use alongside CGWB stage of extraction, not instead of it. (2) Only 402 of 552 districts have ≥ 2 pre-monsoon readings per well in April–June; some states sample at other times. (3) 44 districts show a negative seasonal rise (post-monsoon deeper), from heavy kharif pumping or sparse wells. (4) Basic quality control only: non-numeric values and readings outside 0–300 m dropped (1,506 readings); per-well medians damp outliers. A stricter filter (≥ 2 readings per year, removing stuck or 3-sigma values) is possible later. (5) One record uses the placeholder code 9999 (Yanam) |
| Processing notes | `research/_scripts/nwic_gwl_districts.py`. Spot checks: Sangrur 40 m (very deep; Punjab decline zone), Jaipur 30 m and Jaisalmer 29 m (deep), Ludhiana 15 m, Bhopal 9 m, Patna 5 m, Alappuzha 1.9 m (very shallow coastal aquifer). The 1991–2020 files exist too, for long-term trends (≈ 230 MB) |
