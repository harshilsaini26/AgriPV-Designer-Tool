# SOURCE: NITI Aayog India Climate & Energy Dashboard (ICED), Climate & Environment pages (reviewed, not downloaded)

| Field | Value |
|---|---|
| Dataset ID | D02 / D03 (reviewed only) |
| Publisher / owner | NITI Aayog, with Vasudha Foundation (maintained by Vistaar Digital). Climate data sourced from IMD; emissions from MoEFCC; air quality from CPCB |
| Dataset name and version | ICED "Climate & Environment" section; site "Last Updated: 02-11-2026" |
| URL / access route | https://iced.niti.gov.in/climate-and-environment and https://iced.niti.gov.in/climate-and-environment/climate-variability/rainfall |
| Accessed on (YYYY-MM-DD) | 2026-11-06 |
| Reference year(s) covered | Temperature: decadal means 1901–2000, then annual 2001–2023. Rainfall: same pattern; monthly IMD station maps to 2023 |
| Spatial coverage | All-India; station maps by state (21 states listed) |
| Spatial unit or resolution | **National** annual/seasonal temperature and rainfall; IMD station points on monthly rainfall maps; one monsoon-season (2020) count of districts by rainfall departure category |
| Temporal resolution | Annual / seasonal / monthly |
| Licence | Not stated. A site disclaimer says the data is taken mainly from government sources, with no guarantee of accuracy |
| OK for a public open-source app? | Unknown; not needed |
| Required attribution text | n/a (not used) |
| Citation | NITI Aayog (2026). India Climate & Energy Dashboard. https://iced.niti.gov.in/ |
| Files in this folder | None |
| Units and key column meanings | n/a |
| Known caveats and gaps | **Not downloaded, for three reasons.** (1) Nothing is at district level: values are national or station points, so they cannot fill D02/D03. (2) The dashboard's data API (`icedapi.niti.gov.in`) returns encrypted payloads, so the data was not pulled programmatically, and circumventing that was out of scope. (3) The per-chart "Download XLS" exports are national series that duplicate IMD publications. Better primary sources for D02/D03: IMD gridded rainfall (0.25°) and temperature (1°) from imdpune.gov.in, and IMD district-wise rainfall normals |
| Processing notes | None. If national IMD series are ever needed for context, use the chart's own "Download XLS" button and record the export here |
