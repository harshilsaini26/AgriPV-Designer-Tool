# SOURCE: NRSC Annual Land Cover & Land Use (LCLU-250K): technical document and 2025 map

| Field | Value |
|---|---|
| Dataset ID | D06 |
| Publisher / owner | National Remote Sensing Centre (NRSC), ISRO, Department of Space, Government of India: Soil Resources & Land Use Monitoring Division, under the Natural Resources Census / NNRMS programme |
| Dataset name and version | (a) Technical document "Annual Assessment of Land Cover and Land Use using Multi-Temporal data, for Dissemination through Bhuvan", control no. NRSC-RSA-SR&LUMG-SRLMD-NOV 2025-TR-0002929-V1.0, November 2025, 16 pp. (b) "Land Use Map of India – 2025", single-page map exported from QGIS 3.40 on 2025-12-05 |
| URL / access route | Uploaded by the project owner through the GitHub web UI. Data layer is disseminated on Bhuvan (https://bhuvan.nrsc.gov.in, Thematic Services → LULC 250K); NRSC LCLU atlas 2005-06 to 2022-23: https://www.nrsc.gov.in/nrscnew/assets/pdf/atlas/LCLU/LCLU%20Atlas%20Final%20With%20Cover_March2024.pdf. **Record the exact download page for (b)** |
| Accessed on (YYYY-MM-DD) | ≤ 2026-11-06 (upload date) |
| Reference year(s) covered | Annual series since 2005-06; the map shows 2025 (agricultural year label to confirm) |
| Spatial coverage | All-India |
| Spatial unit or resolution | 56 m raster (≈ 1:250,000), 18 classes |
| Temporal resolution | Annual, with seasonal crop layers (Kharif / Rabi / Zaid) |
| Licence | Document marked "Security classification: Unrestricted; Distribution: General". The data layer itself is governed by Bhuvan's terms (free registration; check re-distribution conditions) |
| OK for a public open-source app? | Document: OK to keep and cite. Data layer: **unknown until Bhuvan terms are checked**. District-level statistics derived from it are lower risk |
| Required attribution text | "Land cover / land use: NRSC, ISRO (Bhuvan LULC 250K)" |
| Citation | NRSC (2025). Annual Assessment of Land Cover and Land Use using Multi-Temporal data: Technical Document, NRSC-RSA-SR&LUMG-SRLMD-NOV 2025-TR-0002929-V1.0. National Remote Sensing Centre, ISRO, Hyderabad |
| Files in this folder | `Landu Use Map of India - Technical Report - 2025.pdf` (778 KB; "Landu" is a typo in the uploaded name), `Land Use Map of India - 2025.pdf` (5.2 MB, map image only, no data). Both committed via web upload even though `.gitignore` excludes `research/**/*.pdf`; acceptable because the document is unrestricted government material |
| Units and key column meanings | 18 classes, including: 1 Built-up; 2 Kharif crop land (Jun–Nov); 3 Rabi crop land (Nov–Apr); 4 Zaid crop land (Apr–Jun); 5 Double/Triple/annual crop land; 6 Current fallow; 7 Plantation/Orchard; 8+ forest, scrub, wasteland, water and snow classes (full table on p. 7 of the technical document) |
| Known caveats and gaps | (1) **The map PDF is a picture, not data**: for D06 we need the raster or district statistics, i.e. the Bhuvan LULC 250K layer (WMS / download), or NRSC's district crop-area statistics. (2) The seasonal classes are exactly what the APV model needs (kharif-only vs double-cropped land), so prioritise getting the raster. (3) 56 m pixels miss small plots |
| Processing notes | None. Next: download the most recent annual LULC raster from Bhuvan (requires a free Bhuvan login, which only you can create), then compute per-district cropland share by season class |
