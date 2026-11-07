# SOURCE: DA&FW Area and Production of Horticulture Crops, Final Estimates 2023-24 and 2024-25

| Field | Value |
|---|---|
| Dataset ID | D10 (horticulture crops missing from UPAg) |
| Publisher / owner | Horticulture Statistics Division, Department of Agriculture & Farmers Welfare (DA&FW), Ministry of Agriculture & Farmers Welfare |
| Dataset name and version | "Area and Production of Horticulture crops for 2024-25 (Final Estimates)" (published 18-03-2026; its Summary sheet also carries the 2023-24 Final column) and "… for 2023-24 (Final Estimates)" (published 07-02-2025) |
| URL / access route | Listing: https://agriwelfare.gov.in/hort-state-level (Documents → State Level). Files: `https://agriwelfare.gov.in/public/sites/default/files/2024_25_Final_Estimates.xls` and `…/2023_24_FinalEstimates.xls` (the site redirects to a signed Google Cloud Storage link, so download with redirects followed) |
| Accessed on (YYYY-MM-DD) | 2026-11-07 |
| Reference year(s) covered | 2023-24 (Final) and 2024-25 (Final). Earlier releases back to 2011-12 are listed on the same page |
| Spatial coverage | All-India and states / UTs |
| Spatial unit or resolution | State (no district values) |
| Temporal resolution | Annual (no season split) |
| Licence | No open licence. DA&FW website policy (checked 2026-11-07): "Material featured on this Website may be reproduced free of charge after taking proper permission by sending a mail to us", reproduced accurately with the source prominently acknowledged (the same wording as UPAg) |
| OK for a public open-source app? | **Restricted until DA&FW grants permission.** The workbooks stay local (git-ignored). Only the national crop areas and yields in `top20_national.csv` are committed: these are the headline All-India figures DA&FW publishes in its own press releases |
| Required attribution text | "Horticulture area and production: Horticulture Statistics Division, Department of Agriculture & Farmers Welfare, Government of India (Final Estimates 2023-24 and 2024-25)" |
| Citation | DA&FW (2026). Area and Production of Horticulture Crops for 2024-25 (Final Estimates). Horticulture Statistics Division, Ministry of Agriculture & Farmers Welfare, New Delhi |
| Files in this folder | Git-ignored, in `raw/dafw_horticulture/`: `2024_25_Final_Estimates.xls` (202 KB, 15 sheets), `2023_24_FinalEstimates.xls` (204 KB, 15 sheets). Committed (derived, national only): `top20_national.csv` |
| Units and key column meanings | Area in **'000 ha**, production in **'000 MT** (coconut by weight, not nut count; flowers loose in '000 MT). Sheets: Summary (all-India by crop), Horticulture (state totals by group), Fruits, Citrus, Vegetables, Plantation, Spices and Flowers (state × crop area A and production P), plus UT sheets |
| Known caveats and gaps | (1) **State level only**: district horticulture area needs the DES APY portal (restricted, ends 2022-23; see `SOURCE_CANDIDATES.md`). (2) No season split, though potato and onion are mainly rabi (onion also has kharif and late-kharif crops). (3) Area in a given year can shift sharply (onion 15.4 → 19.7 lakh ha from 2023-24 to 2024-25), so use the two-year mean. (4) Perennial orchards (mango, coconut, cashew, arecanut) are counted at their full planted area |
| Processing notes | `research/_scripts/national_crop_ranking.py` (xlrd) reads the Summary sheet, averages the two Final columns, drops group totals and "Other …" rows, and merges the result with the UPAg field crops. All-India totals: horticulture 290.86 lakh ha (2023-24) and 301.36 lakh ha (2024-25) |
