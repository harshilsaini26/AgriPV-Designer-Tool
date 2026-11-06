# SOURCE: CGWB National Compilation on Dynamic Ground Water Resources of India, 2024 (district table)

| Field | Value |
|---|---|
| Dataset ID | D07 |
| Publisher / owner | Central Ground Water Board (CGWB), Department of Water Resources, RD & GR, Ministry of Jal Shakti, with State/UT nodal departments |
| Dataset name and version | "National Compilation on Dynamic Ground Water Resources of India, 2024" (488 pp.). **Annexure II: District-wise Ground Water Resources Availability, Utilization and Stage of Extraction (2024)**, PDF pages 169–206 |
| URL / access route | Publication page https://cgwb.gov.in/cgwbpnm/publication-detail/1326, file https://cgwb.gov.in/cgwbpnm/download/1326 |
| Accessed on (YYYY-MM-DD) | 2026-11-06 |
| Reference year(s) covered | Assessment year 2024 (domestic allocation projected to 2025) |
| Spatial coverage | All-India: 36 states/UTs, **715 districts** |
| Spatial unit or resolution | District (assessment units are blocks / mandals / taluks; district totals here) |
| Temporal resolution | Assessment cycle (annual since 2022) |
| Licence | Not stated in the report. It is a public Government of India publication, freely downloadable; earlier assessments are on data.gov.in under GODL |
| OK for a public open-source app? | Likely OK with attribution (public government report); confirm the GODL listing for the 2024 edition |
| Required attribution text | "Ground water resources: Central Ground Water Board, Ministry of Jal Shakti, Dynamic Ground Water Resources of India 2024" |
| Citation | CGWB (2024). National Compilation on Dynamic Ground Water Resources of India, 2024. Central Ground Water Board, Ministry of Jal Shakti, Faridabad |
| Files in this folder | Committed: `cgwb_dgwr_2024_district.csv` (715 rows). Git-ignored: `raw/cgwb_national_compilation_dgwr_2024.pdf` (10.2 MB) |
| Units and key column meanings | All volumes in **hectare-metres (ham)**. `recharge_monsoon_rainfall_ham`, `recharge_monsoon_other_ham`, `recharge_nonmonsoon_rainfall_ham`, `recharge_nonmonsoon_other_ham`, `total_annual_recharge_ham`, `total_natural_discharges_ham`, `annual_extractable_resource_ham`, `extraction_irrigation_ham`, `extraction_industrial_ham`, `extraction_domestic_ham`, `extraction_total_ham`, `allocation_domestic_2025_ham`, `net_availability_future_ham`, `stage_of_extraction_pct` (extraction ÷ extractable × 100; CGWB categories: ≤ 70 Safe, 70–90 Semi-critical, 90–100 Critical, > 100 Over-exploited), `pdf_page` |
| Known caveats and gaps | (1) **State and district names lost their spaces in the PDF text** ("UTTARPRADESH", "AlluriSitharamaRaju"); match to LGD with a whitespace-insensitive comparison. (2) Validation: extraction components sum to the total for all 715 rows, and the stage of extraction equals extraction ÷ resource for all rows. **25 rows** (mostly Punjab, plus Patna and Kakinada) have recharge − discharge ≠ extractable resource; this looks like a feature of the source (CGWB's environmental-flow adjustments), not a parsing error, but spot-check against the PDF. (3) District totals hide block-level hotspots: Annexure III(B) has block categorisation counts per district, not yet extracted. (4) Groundwater status matters for APV because PM-KUSUM pump solarisation and irrigated vs rainfed cropping depend on it |
| Processing notes | `research/_scripts/parse_cgwb_annexure2.py` (PyMuPDF). The PDF text layer moves each decimal point to the end of the number, so cell values are rebuilt from characters sorted by x position |
