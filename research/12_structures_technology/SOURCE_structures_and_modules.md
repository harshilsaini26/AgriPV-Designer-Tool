# SOURCE: Structure presets (geometry, farmable fraction) and module parameters

| Field | Value |
|---|---|
| Dataset ID | D24 |
| Publisher / owner | Structures: Fraunhofer ISE agrivoltaics guideline (2022) and the DIN SPEC 91434:2021-05 land-loss caps it summarises; preset choices are AgriPV Lab's own. Modules: Polycab India, Onix Renewable and Emmvee datasheets |
| Dataset name and version | `structure_presets.csv` (7 presets) and `module_parameters.csv` (bifacial TOPCon and monofacial PERC) |
| URL / access route | Fraunhofer ISE, *Agrivoltaics: Opportunities for Agriculture and the Energy Transition*, 2nd ed., April 2022 (copy read: https://helapco.gr/xoorigle/2023/10/07_APV-Guideline_Fraunhofer.pdf). Datasheets: https://cms.polycab.com/media/sb2mnl4w/polycab_pv-module-g2g-topcon.pdf, https://www.onixrenewable.com/upload/download-center/N-TYPE_TOPCON(580WP-590WP).pdf, https://emmvee.com/pdf/MonoPER-Half-Cut-Module.pdf |
| Accessed on (YYYY-MM-DD) | 2026-11-14 |
| Reference year(s) covered | Datasheets current in 2026; Fraunhofer guideline 2022 |
| Spatial coverage | National defaults |
| Spatial unit or resolution | Per preset / per module option |
| Temporal resolution | One-off |
| Licence | Guideline and datasheets are copyrighted; only technical facts (dimensions, ratings, caps) are extracted, with citation. PDFs stay local in `raw/` |
| OK for a public open-source app? | OK (facts with citation) |
| Required attribution text | "Structure presets: AgriPV Lab, using DIN SPEC 91434 land-loss caps (via Fraunhofer ISE 2022). Module parameters: manufacturer datasheets (Polycab, Onix, Emmvee)" |
| Citation | Trommsdorff, M. et al. (2022). *Agrivoltaics: Opportunities for Agriculture and the Energy Transition*, 2nd ed. Fraunhofer ISE, Freiburg. DIN SPEC 91434:2021-05, *Agri-photovoltaic systems — Requirements for primary agricultural use* |
| Files in this folder | Committed: `structure_presets.csv`, `module_parameters.csv`. Git-ignored: `raw/datasheets/` (3 datasheet PDFs) |
| Units and key column meanings | Structures: `clearance_m` (lower module edge; for trackers, at the 55° limit), `hub_height_m`, `collector_width_m` (module slope width used in the GCR), `gcr_definition`, `a_farm_central/low/high` (farmable fraction of the plot), `din_spec_91434_category`. Modules: efficiency (%), bifaciality (%), Pmax temperature coefficient (%/°C), NOCT (°C), dimensions (mm), degradation (%/yr) |
| Known caveats and gaps | (1) **`a_farm` values are assumptions** set within the DIN SPEC 91434 caps: land loss of at most 10% for overhead systems (category I) and 15% for interspace systems (category II). No Indian measurement of farmable fraction was found. (2) **Preset geometry is partly our choice**: lower-edge heights for the reference and vertical presets, 2-in-portrait tables, and the 10–25° tilt band are assumptions, not standards. (3) **Machinery notes are indicative**, from German practice: 3.2 m clearance suits standard machinery, and Heggelbach's 5 m suits combine harvesters. Indian tractor heights should be checked against spec sheets. (4) Modules: three datasheets from three manufacturers. Bifaciality is 80% ± 10% from one (Onix); the ALMM list should be checked when the model is used |
| Processing notes | Default physics inputs: bifacial efficiency 22.5%, bifaciality 0.80, γ = −0.30%/°C; monofacial efficiency 21.0%, γ = −0.35%/°C; module 2,278 × 1,134 mm (2.58 m²). Tracker clearance = hub height − 1.139 m × sin 55°. The structure presets match spec §12.1 (3 fixed heights × 2 module options, 2 tracker heights × 2 module options, and vertical bifacial) |
