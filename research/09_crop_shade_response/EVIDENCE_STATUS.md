# D16 crop shade response: evidence status (draft, updated 2026-11-14)

How far the shade-response evidence goes for the 20 research crops, what the first parameters are, and what to
find next. The model curve and grades are in the product spec (§12, §13); the requirements are in
[`DATA_REQUIREMENTS.md` (D16)](../DATA_REQUIREMENTS.md).

## Files

| File | What it holds |
|---|---|
| [`extraction/shade_response_extraction.csv`](extraction/shade_response_extraction.csv) | 207 treatment rows: 32 read by hand from 6 papers, 175 from the Laub et al. (2022) data set |
| [`papers/bibliography.csv`](papers/bibliography.csv) | The 7 sources, with DOI, study type and licence (PDFs stay local) |
| [`papers/SOURCE_laub_2022_shade_metaanalysis.md`](papers/SOURCE_laub_2022_shade_metaanalysis.md) | Source card for the meta-analysis data set (CC BY 4.0) |
| [`parameters/group_curves_laub2022.csv`](parameters/group_curves_laub2022.csv) | `(L_t, k)` per crop type, fitted to the meta-analysis means and 95% CI |
| [`parameters/crop_parameters_draft.csv`](parameters/crop_parameters_draft.csv) | Draft `(L_t, k)` low / central / high and grade for each research crop |

Scripts: `_scripts/build_shade_extraction.py`, then `_scripts/fit_shade_parameters.py`.

## Method (draft)

- **Light** is the season-mean fraction reaching the crop relative to open field (`L_s` in the model), the same
  quantity the app's physics computes. Each row records how it was obtained in `light_basis`:
  - `measured_season`: measured under the treatment over the season (IARI wheat, Heggelbach, Japan).
  - `modelled_season`: computed from the published layout where the paper gives only spot readings (CAZRI; see
    below).
  - `nominal_cover`: 1 − panel cover ratio (Korea).
  - `compiled`: as compiled in the meta-analysis.
  - `nominal_net_inconsistent`: a net rating that the yields show is wrong (Raichur). **Excluded from fitting.**
- **CAZRI light.** The paper gives midday PAR only in the shaded part of the interspace (0.41–0.58 of open field).
  `_scripts/cazri_interspace_light.py` models season-mean light over the whole cropped interspace from the
  published layout. That layout is: east–west rows tilted 26° south, 0.99 × 1.64 m modules, two- and three-module-deep
  arrays with 6.4 and 9.6 m clear gaps, and the top row at 60% density. It uses Jodhpur sun paths, clear-sky
  irradiance and a monthly diffuse share. Results: **0.91 for kharif (Jul–Sep), 0.77 for rabi (Nov–Feb)**. Two
  inputs are not published: the lower-edge height (0.75 m assumed) and module orientation (portrait assumed).
  Varying them (0.5–1.5 m, portrait or landscape) gives 0.87–0.94 and 0.65–0.86. Checks: transparent panels give 1.0,
  and the modelled noon shadow matches hand geometry.
- **IARI light** uses the global radiation measured under each net on 8 dates (Table 1 of the paper). The values
  are 0.78/0.65/0.47/0.26 (2014-15) and 0.74/0.60/0.43/0.24 (2015-16) for nets rated 20/35/50/75%, close to the
  ratings.
- **Group curves** come from the meta-analysis predictions (Table S2) for each crop type, fitted over light
  0.4–0.95. Central uses the mean, low uses the lower 95% bound and high the upper bound.
- **Crop curves** replace the group curve only where a crop has at least 8 points from 3 studies covering 0.3 of the
  light range (wheat, soybean and maize so far). They keep the group's low–high spread.
- **Grades** follow spec §13.3. A crop with no group curve and too few points to fit gets D.

## Draft parameters

| Crop | Grade | L_t central | k central | Basis | Indian evidence |
|---|---|---|---|---|---|
| Rice | C | 0.96 | 1.06 | C3 cereal group; Korea APV checks it (0.81 and 0.91 at about 30% shade) | none yet |
| Wheat | B | 0.86 | 1.36 | Own fit, 47 points, 12 studies | IARI Delhi shade nets (measured light) |
| Soybean | B | 1.00 | 1.18 | Own fit, 56 points, 10 studies | IARI shade nets (in meta-analysis) |
| Cotton | **D** | — | — | No data, no close group | none |
| Maize | B | 1.00 | 1.24 | Own fit, 51 points, 10 studies | none |
| Gram (chickpea) | B | 1.00 | 1.22 | Grain-legume group; the CAZRI point sits 0.21 above it | CAZRI Jodhpur APV |
| Mustard | **D** | — | — | No data, no close group | none |
| Bajra | C | 1.00 | 1.32 | Maize (C4) group, borrowed | none |
| Sugarcane | **D** | — | — | No data, no close group | none |
| Moong | B | 1.00 | 1.22 | Grain-legume group; the CAZRI point sits 0.06 above it | CAZRI Jodhpur APV |
| Groundnut | C | 1.00 | 1.22 | Grain-legume group | none |
| Tur | C | 1.00 | 1.22 | Grain-legume group | Raichur shade nets (excluded: light unreliable) |
| Jowar | C | 1.00 | 1.32 | Maize (C4) group, borrowed | none |
| Urad | C | 1.00 | 1.22 | Grain-legume group | Raichur shade nets (excluded: light unreliable) |
| Guar | B | 1.00 | 1.22 | Grain-legume group; the CAZRI point sits on it | CAZRI Jodhpur APV |
| Potato | B | 0.96 | 1.10 | Tuber group | none |
| Onion | C | 0.96 | 1.10 | Tuber group, borrowed for a bulb crop | none |
| Lentil | C | 1.00 | 1.22 | Grain-legume group | none |
| Sesame | **D** | — | — | No data, no close group | none |
| Cumin | **D** | — | — | One CAZRI point (89% at 0.77 light), no group to anchor a curve | CAZRI Jodhpur APV |

**Against the spec targets (§7.3):** the top 10 crops should be grade B or better, but only 5 are (wheat, soybean,
maize, gram, moong). Cotton, mustard and sugarcane are D, and rice and bajra are C. The other 10 crops should be grade C or better;
sesame and cumin are D. Guar rose to B with the modelled CAZRI light; tur and urad fell to C when the Raichur rows
were excluded.

## What the evidence says so far

1. **The meta-analysis curves are steep.** Grain legumes and maize lose yield from the first bit of shade (`L_t` = 1);
   C3 cereals and potato hold to about 4% shade. At 70% light the curves give about 72% (C3 cereals), 63%
   (grain legumes) and 61% (maize).
2. **Most of the apparent Indian advantage was the light metric.** On spot readings, CAZRI's chickpea and cumin
   looked very shade-tolerant (93% and 89% of yield at 47% and 57% light). With season-mean light over the
   cropped strip, the kharif legumes fall onto the grain-legume curve (moong 0.95 against 0.89 predicted, guar
   0.88 against 0.89). Chickpea's gap to the curve shrinks from 0.58 to 0.21 but does not close: it kept 93% at 0.77 light,
   where the curve gives 72%. Even at the brightest light the layout allows (0.86), the curve gives 83%. So winter
   chickpea in Jodhpur may genuinely tolerate shade better, perhaps because irrigated rabi crops there are
   close to light saturation. One site and one season cannot settle it.
3. **Shade-net ratings need checking against measured light.** IARI's measured light was close to its net
   ratings, but at Raichur the 75% net gave the same yield as the 50% net, so those ratings cannot be trusted.
4. **Indian wheat is more sensitive than the C3 curve.** Under IARI's shade nets in Delhi, wheat dropped to 66–78% of yield at 20%
   shade (measured light 0.74–0.78), worse than the meta-analysis C3 curve. The winter crop grows in lower light (fog, short days), which may explain it.
5. **Year-to-year swings are large.** The same APV gave +3% and −19% for wheat and +11% and −18% for potato in
   Germany (dry vs wet years), and Korea's soybean fell to 31% in a very wet year. The low–high range has to
   carry this.

## Next research, in priority order

1. **Cotton, mustard and sugarcane** (top-10 crops at D). Look for season-long shade-net or agroforestry trials
   (cotton under shade in China and India; mustard under poplar or shade nets in Punjab, Haryana and Jhansi;
   sugarcane intercropped or under shade in Brazil and India) and any APV trials.
2. **Rice from India** (NRRI Cuttack low-light trials; KrishiKosh theses), plus the six-year Japanese APV trial
   (Chikusei 2018–2023, *Field Crops Research*, 23% loss at 27% panel cover; DOI to confirm).
3. **Bajra and jowar** shade or intercrop trials (ICRISAT, AICRP), to replace the borrowed maize curve.
4. **Sesame, lentil, groundnut, onion, potato and cumin** from Indian or tropical trials.
5. **Confirm the CAZRI layout and light.** CAZRI's light-map paper (Santra, Meena and Yadav 2021, *Biosystems
   Engineering*, doi:10.1016/j.biosystemseng.2021.06.017) maps daily light for the same plant: 0–5 mol/m²/day
   below the panels, 5–20 in partly shaded and 20–30 in unshaded interspace. It is paywalled, and ICAR's repository
   (krishi.icar.gov.in) could not be reached from here. If you can get the PDF, its edge height and light maps would
   replace the modelled values. For Raichur, find measured light under its nets (the authors' thesis on KrishiKosh).
6. **Freeze a hold-out set** for validation (D17) once there are at least 30 Indian points across 8 crops. The
   `used_for` column is "unassigned" until then.

The ICAR-CAZRI programme is the strongest Indian lead. Its other papers (Santra et al. 2017, 2018 and 2020; Poonia
et al. 2021 in *Indian Farmer*) may hold more crop-by-design yields.
