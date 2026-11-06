# SOURCE: MNRE PM-KUSUM guidelines and office memoranda (Component A focus)

| Field | Value |
|---|---|
| Dataset ID | D19 |
| Publisher / owner | Ministry of New and Renewable Energy (MNRE), Government of India: National Portal for PM-KUSUM |
| Dataset name and version | Key document: **"Comprehensive guidelines of the PM-KUSUM dated 17.01.2024"** (73 pp.; consolidates all earlier amendments). Also: OMs dated 2026-09-28 (scanned), 2026-04-26 (revised PBI claim format, Comp A), extension of timelines for financial closure (image), escrow/LC advisory, bank lending guidelines for farmers' solar plants, 2021-12-14 simplification, amendments/clarifications, 2020-11-09 scale-up, 2019-07-22 original guidelines, 2019-03-08 administrative approval |
| URL / access route | https://pmkusum.mnre.gov.in/#/comp-Documents. Files: `https://apipmk.mnre.gov.in/api/Master_Document_Landing/SliderImage?docid=<id>&docspid=41` (ids 115, 207, 205, 199, 196, 108, 109, 104, 103, 101, 100) |
| Accessed on (YYYY-MM-DD) | 2026-11-06 |
| Reference year(s) covered | 2019 to 2026 |
| Spatial coverage | All-India (state tariffs and implementation are set by state DISCOMs / SERCs) |
| Spatial unit or resolution | National rules |
| Temporal resolution | As issued |
| Licence | Government of India public documents |
| OK for a public open-source app? | OK to cite and to encode the rules; the PDFs themselves stay local (git-ignored) |
| Required attribution text | "PM-KUSUM rules: MNRE, Comprehensive Guidelines (17 Jan 2024) and subsequent OMs" |
| Citation | MNRE (2024). Comprehensive Guidelines for implementation of PM-KUSUM Scheme, 17 January 2024. New Delhi |
| Files in this folder | Committed: `kusum_component_a_rules.md` (extracted rules with page/section references). Git-ignored: `raw/mnre_docs/*.pdf` (11 documents) and `raw/mnre_docs/extension_timeline_financial_closure.jpg` (the "PDF" served for doc 199 is a JPEG image) |
| Units and key column meanings | See `kusum_component_a_rules.md` |
| Known caveats and gaps | (1) The **2026-09-28 OM is a scanned image with no text layer**: read it manually (or OCR it) because it may change Component A terms. (2) The guidelines describe the scheme as running "till March 2026"; check the later OMs for the current sanction / extension status. (3) Levelised tariffs are fixed by each state (SERC orders) and are **not** in these documents: collect state tariff orders separately (D19 open item) |
| Processing notes | Text extracted with PyMuPDF; rules summarised by hand in `kusum_component_a_rules.md` |
