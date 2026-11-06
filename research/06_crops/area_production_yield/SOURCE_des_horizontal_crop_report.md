# SOURCE: DES "Horizontal Crop Vertical Year" district APY report (incl. horticulture), 2017-18 to 2022-23

| Field | Value |
|---|---|
| Dataset ID | D10 (fills part of the horticulture gap in the UPAg export) |
| Publisher / owner | Directorate of Economics & Statistics (DES), Department of Agriculture & Farmers Welfare (crop production statistics system) |
| Dataset name and version | Report "Horizontal_Crop_Vertical_Year_Report" (HTML table saved with an `.xls` extension), whole-year district APY for 41 crops |
| URL / access route | Uploaded by the project owner through the GitHub web UI. The format matches the DES Crop Production Statistics Information System report builder (https://data.desagri.gov.in / https://aps.dac.gov.in, "District wise" → "Horizontal Crop / Vertical Year"). **Record the exact URL and the filter selections used** |
| Accessed on (YYYY-MM-DD) | ≤ 2026-11-06 (upload date) |
| Reference year(s) covered | 2017-18 to 2022-23 |
| Spatial coverage | **26 states/UTs only**, 541 districts. Missing, among others: Uttar Pradesh, Telangana, Odisha, Jharkhand, Delhi, Sikkim, Ladakh, Chandigarh, Dadra & Nagar Haveli and Daman & Diu, Lakshadweep |
| Spatial unit or resolution | District (names, numbered "1. Nicobars"; no LGD codes) |
| Temporal resolution | Annual, season = "Whole Year" only |
| Licence | Government of India data; no licence stated in the file. DES data is also published on data.gov.in under the Government Open Data Licence – India (GODL) |
| OK for a public open-source app? | Probably OK with attribution under GODL if the same series is taken from data.gov.in; otherwise **unknown**. The raw report is already public in this repo (web upload) |
| Required attribution text | "Crop area, production and yield: Directorate of Economics & Statistics, DA&FW, Government of India" |
| Citation | DES, DA&FW (2026). District-wise Area, Production and Yield, 2017-18 to 2022-23 (Horizontal Crop / Vertical Year report) |
| Files in this folder | `Horizontal_Crop_Vertical_Year_Report.xls` (14 MB HTML, committed by upload). Git-ignored: `raw/des_horizontal_report_long.csv` (46,619 values, tidy long format) |
| Units and key column meanings | Long CSV: `state`, `district`, `crop_year`, `crop`, `season`, `metric` (Area / Production / Yield), `unit`, `value`. Units: Area in hectares; Production in tonnes (**coconut in nuts**; check cotton (bales?), jute and mesta in the header units); Yield in tonnes/ha (coconut: nuts/ha). Crops: Banana, Coconut, Tapioca, Black pepper, Sugarcane, Dry chillies, Ginger, Potato, Turmeric, Onion, Sweet potato, Tobacco, Coriander, Garlic, Cotton (lint), Jowar, Sunflower, Cashewnut, Arecanut, Mango, Other fresh fruits, Other vegetables, Pineapple, Guar seed, Sannhamp, Wheat, Maize, Gram, Groundnut, Ragi, Rapeseed & Mustard, Sesamum, Small millets, Cardamom, Dry ginger, Arecanut (processed), Mesta, Arhar/Tur, Castor seed, other oilseeds, Cond-spcs other |
| Known caveats and gaps | (1) Partial state coverage (see above) and no Rice, Bajra, Soybean, Moong or Urad columns, so the crop selection looks filtered; **re-run the report for all states and all crops** if possible. (2) Season is aggregated to "Whole Year", so it cannot be used for season-level rotation shares. (3) Units differ by crop (nuts vs tonnes); always read the `unit` column. (4) Yield here is t/ha, while UPAg uses kg/ha |
| Processing notes | Converted with `research/_scripts/parse_des_horizontal_report.py` (reads the three-row header; handles State/District rowspans). Use alongside `SOURCE_upag_des_district_apy.md`: UPAg for field crops by season, this report for horticulture (onion, potato, chillies, garlic, ginger, turmeric, banana, other vegetables) |
