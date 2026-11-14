# SOURCE: Laub et al. (2022) shade-response meta-analysis and its data set

| Field | Value |
|---|---|
| Dataset ID | D16 |
| Publisher / owner | M. Laub, L. Pataczek, A. Feuerbacher, S. Zikeli, P. Högy (University of Hohenheim); published by Springer in *Agronomy for Sustainable Development* |
| Dataset name and version | "Contrasting yield responses at varying levels of shade suggest different suitability of crops for dual land-use systems: a meta-analysis", *Agron. Sustain. Dev.* 42, 51 (2022). Supplementary ESM 1 (Table S1: the 58 studies; Table S2: predicted yield and 95% CI per crop type at 5–90% shade) and ESM 2 (data set: 428 shade-level × yield points) |
| URL / access route | Article: https://doi.org/10.1007/s13593-022-00783-7. ESM: `https://media.springernature.com/original/springer-static/esm/art%3A10.1007%2Fs13593-022-00783-7/MediaObjects/13593_2022_783_MOESM1_ESM.docx` and `…MOESM2_ESM.xlsx` |
| Accessed on (YYYY-MM-DD) | 2026-11-14 |
| Reference year(s) covered | Studies published up to about 2021 |
| Spatial coverage | Temperate and subtropical sites worldwide (mainly China, Europe, North America, Iran, Australia); one Indian study (Jumrani & Bhatia 2020, soybean) |
| Spatial unit or resolution | Field or pot experiments (point locations with latitude and longitude) |
| Temporal resolution | One-off experiments |
| Licence | **CC BY 4.0** (article: "This article is licensed under a Creative Commons Attribution 4.0 International License"; the ESM is part of the article) |
| OK for a public open-source app? | **OK** with attribution |
| Required attribution text | "Shade-response data: Laub, M. et al. (2022), Agronomy for Sustainable Development 42, 51, doi:10.1007/s13593-022-00783-7 (CC BY 4.0)" |
| Citation | Laub, M., Pataczek, L., Feuerbacher, A., Zikeli, S., Högy, P. (2022). Contrasting yield responses at varying levels of shade suggest different suitability of crops for dual land-use systems: a meta-analysis. *Agronomy for Sustainable Development* 42, 51 |
| Files in this folder | Git-ignored: `laub_2022_shade_metaanalysis.pdf`, `raw/laub_2022_esm1.docx`, `raw/laub_2022_esm2.xlsx`. Derived and committed: the Laub rows of `../extraction/shade_response_extraction.csv` (crops on the research list or standing in for it) and `../parameters/group_curves_laub2022.csv` |
| Units and key column meanings | ESM 2: `Crop`, `Crop_type`, `RSR (%)` (reduction in solar radiation vs unshaded), `Yield (%)` (of unshaded control), `Experiment_type` (artificial shading / intercropping), `Climatic_zone`, `Latitude`, `Longitude`, `GHI_kWh_m2`, `Shade_type`, `Reference`, `DOI`. In our extraction, light fraction = 1 − RSR/100 and relative yield = Yield/100 |
| Known caveats and gaps | (1) **Temperate and subtropical only**, with lower sunlight than most of India (site GHI about 870–2,120 kWh/m²/yr in Table S1, against roughly 1,700–2,200 across most Indian cropland); at India's higher light, a given shade cut may cost less yield because crops are closer to light saturation. (2) Mostly shade nets and intercropping, few agrivoltaic trials. (3) Crop types, not crops: no cotton, mustard, sugarcane, sesame, cumin, rice or Indian pulses. (4) The group curves exceed 100% for berries, fruits and fruity vegetables at moderate shade; our model caps relative yield at 1. (5) Light is "reduction in solar radiation" as each study reported it (net rating or measured), not a common metric |
| Processing notes | `research/_scripts/build_shade_extraction.py` keeps the relevant ESM 2 rows; `research/_scripts/fit_shade_parameters.py` fits the spec §12 curve to Table S2 per crop type (central = mean, low / high = 95% CI bounds) over light fractions 0.4–0.95 |
