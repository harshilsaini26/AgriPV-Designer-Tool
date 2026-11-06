# SOURCE: Global Macro Database (GMD), India series

| Field | Value |
|---|---|
| Dataset ID | D21 (inflation, interest rates, exchange rate: macro context for discount rates and escalation) |
| Publisher / owner | Global Macro Database project, Karsten Müller and co-authors (KMueller-Lab) |
| Dataset name and version | GMD release **v2026_09** (latest at access; package version 2.0.0) |
| URL / access route | Country page: https://www.globalmacrodata.com/india/. Release file `GMD_2026_09.dta` fetched from the project's public release bucket (`gmd-releases.s3.ap-southeast-2.amazonaws.com/data/distribute/`), which is the same path the official `global_macro_data` Python package uses. The website's own download form asks for an email address; it was not used |
| Accessed on (YYYY-MM-DD) | 2026-11-06 |
| Reference year(s) covered | India series 1800–2031 (values after 2025 are forecasts) |
| Spatial coverage | India (national) |
| Spatial unit or resolution | Country |
| Temporal resolution | Annual |
| Licence | **GMD Research Use Terms:** free for academic use, teaching, and non-profits' non-commercial work. Companies need written permission. "Not for products: do not build any part of it, even in derived form, into a product, service, model…". No re-hosting or republishing |
| OK for a public open-source app? | **Restricted. Do not ship any GMD value or derivative in AgriPV Lab, and do not commit the data.** Use it only as a local research reference. For app defaults, use primary public sources: RBI (repo rate, G-sec yields, DBIE), MoSPI CPI, CERC/SERC orders |
| Required attribution text | Cite the GMD paper whenever its numbers are referenced |
| Citation | Müller, K., Xu, C., Lehbib, M. & Chen, Z. (2025). The Global Macro Database: A New International Macroeconomic Dataset. NBER Working Paper 33714 |
| Files in this folder | Git-ignored: `raw/gmd/GMD_2026_09_IND.csv` (India rows only, 232 years × 162 columns), `raw/gmd/versions.csv`. The full 59 MB global file was deleted after extraction |
| Units and key column meanings | `year`; `infl` CPI inflation %; `CPI` index; `cbrate` central-bank policy rate %; `strate` short-term rate %; `ltrate` long-term (10-y govt) rate %; `USDfx` INR per USD; `deflator` (2015 = 100); `forecast_*` columns hold projections. Recent values: 2024 infl 4.63 %, cbrate 6.50 %, ltrate 6.86 %, USDfx 83.67 |
| Known caveats and gaps | (1) Licence blocks any use inside the product (see above). (2) Annual national aggregates, with no lending rates for agri/solar loans, so D21 still needs SBI/NABARD/IREDA loan terms and the CBDT depreciation schedule. (3) Values from 2026 on are forecasts |
| Processing notes | India rows extracted with pandas (`ISO3 == "IND"`) in a throwaway environment; the extraction script was not kept because nothing derived from GMD is committed |
