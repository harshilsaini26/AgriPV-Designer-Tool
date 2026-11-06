# SOURCE: Farm Harvest Prices of Principal Crops in India, 2022-23 (DES / DA&FW)

| Field | Value |
|---|---|
| Dataset ID | D13 (realised farm-gate prices; complements MSP) |
| Publisher / owner | Agricultural Marketing Division, Department of Agriculture & Farmers Welfare (published by DES), Government of India |
| Dataset name and version | "Farm Harvest Prices of Principal Crops in India 2022-23", April 2024, 229 pp. |
| URL / access route | https://desagri.gov.in/wp-content/uploads/2024/04/FHP-Publication-for-the-Year-2022-23.pdf (earlier years: FHP 2015-16 to 2018-19 on desagri.gov.in) |
| Accessed on (YYYY-MM-DD) | 2026-11-06 |
| Reference year(s) covered | 2019-20 to 2022-23 (state averages in the summary tables); 2022-23 district / centre tables in the state sections |
| Spatial coverage | All major states (state sections 4.1 onwards) |
| Spatial unit or resolution | State averages; district-level centre prices within state tables |
| Temporal resolution | Annual (harvest marketing period of 6–8 weeks after harvest begins, fixed per crop and state) |
| Licence | Government of India publication; no licence stated |
| OK for a public open-source app? | Likely OK with attribution (official statistics); confirm before shipping derived values |
| Required attribution text | "Farm harvest prices: DA&FW, Government of India (FHP 2022-23)" |
| Citation | DA&FW (2024). Farm Harvest Prices of Principal Crops in India 2022-23. Agricultural Marketing Division, New Delhi |
| Files in this folder | Committed: `fhp_state_major_crops_2019-2023.csv` (Table 2: 9 major crops: paddy, wheat, maize, bajra, gram, tur/arhar, groundnut, mustard, sesamum; state × year; 250 values; `pdf_page` for checking). Git-ignored: `raw/FHP-Publication-for-the-Year-2022-23.pdf` (12.2 MB) |
| Units and key column meanings | ₹ per quintal. Farm harvest price = average wholesale price at which producers sell to traders at the village site during the specified post-harvest marketing period |
| Known caveats and gaps | (1) Tables are in a bilingual PDF and need extraction (PyMuPDF, as for CGWB). (2) Many cells are "NR" (not reported). (3) Covers principal field crops plus some horticulture (check the onion / potato tables); 2022-23 is the latest edition found |
| Processing notes | Table 2 extracted with `research/_scripts/parse_fhp_summary.py` ("NR" → blank). Still to do: Table 3 (pp. 12–103, all principal crops × variety × season × state) and Table 4 (district-wise 2022-23), which need a column-aware parser. Plan: FHP as the **central** realised price, MSP as the optimistic case for MSP crops |
