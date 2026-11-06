# SOURCE: Cost of Cultivation of principal crops (DES CCS), via India Data Portal

| Field | Value |
|---|---|
| Dataset ID | D12 |
| Publisher / owner | Original: Directorate of Economics & Statistics (DES), DA&FW: Comprehensive Scheme for Studying the Cost of Cultivation of Principal Crops in India (CCS). Compiled and hosted by India Data Portal (ISB Bharti Institute of Public Policy) |
| Dataset name and version | India Data Portal dataset `cost-of-cultivation` (CKAN id `41388795-3e3d-4c7e-82dc-d36335ad18b9`), resource `cost-of-cultivation.csv`, metadata modified 2026-07-17 |
| URL / access route | https://ckandev.indiadataportal.com/dataset/cost-of-cultivation. CSV: `…/resource/be22e37e-acfc-43a9-859c-d4a066489a69/download/cost-of-cultivation.csv`. Upstream: https://desagri.gov.in/document-report-category/cost-of-cultivation-production-estimates-archive |
| Accessed on (YYYY-MM-DD) | 2026-11-06 |
| Reference year(s) covered | 1996-97 to 2021-22 (26 crop years; densest 2017-18 to 2021-22) |
| Spatial coverage | Major producing states per crop (e.g. Maharashtra 363 rows, Uttar Pradesh 338, Karnataka 325) |
| Spatial unit or resolution | **State** × crop × year (CCS sample-based estimates) |
| Temporal resolution | Annual |
| Licence | **Open Data Commons Attribution License (ODC-By)**, as listed on India Data Portal |
| OK for a public open-source app? | OK with attribution |
| Required attribution text | "Cost of cultivation: Directorate of Economics & Statistics, DA&FW (CCS), via India Data Portal (ODC-By)" |
| Citation | DES, DA&FW. Cost of Cultivation/Production estimates of principal crops, 1996-97 to 2021-22. Compiled by India Data Portal, ISB (2026) |
| Files in this folder | Committed: `idp_des_cost_of_cultivation_1996-2022.csv` (1.7 MB, 3,880 rows). Git-ignored: `raw/india_data_portal/cost-of-cultivation.csv` (identical), `raw/india_data_portal/package.json` (CKAN metadata) |
| Units and key column meanings | ₹ per hectare unless noted. `cul_cost_a1 … cul_cost_c2`, `cul_cost_c2rev`, `cul_cost_a2fl`: cost of cultivation (₹/ha) by CACP cost concept (A2 = paid-out costs; A2+FL adds family labour (used for MSP); C2 adds imputed rent on owned land and interest on owned capital); `prod_cost_*`: cost of production (₹/quintal); `main_product_value`, `by_product_value` (₹/ha); `derived_yield` (quintal/ha); `opr_cost_*` / `fix_cost_*` itemised operational and fixed costs (₹/ha); `hmn_lab_hrs_*` labour hours/ha; `num_holdings_sample`, `num_tehsils_sample`; `crop_code`, `state_code` (Census 2011 state code) |
| Known caveats and gaps | (1) State level only, so district values must be inherited from the state. (2) Latest year is 2021-22; inflate to the analysis year with the CPI-AL or WPI agricultural input index. (3) `cul_cost_a2fl` is blank for older years. (4) **Field crops only**: no onion, potato or vegetable costs; for those use NHRDF / state horticulture department cost norms or NABARD scale-of-finance tables. (5) Sample sizes per state-crop can be small (`num_holdings_sample`) |
| Processing notes | Copied as-is. Planned: choose C2 (full economic cost) and A2+FL (cash plus family labour) as the two farmer-income cost bases for D12; use the latest 3-year average per state × crop |
