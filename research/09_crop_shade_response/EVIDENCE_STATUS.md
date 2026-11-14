# D16 crop shade response: evidence status (draft, updated 2026-11-14)

How far the shade-response evidence goes for the 20 research crops, what the first parameters are, and what to
find next. The model curve and grades are in the product spec (§12, §13); the requirements are in
[`DATA_REQUIREMENTS.md` (D16)](../DATA_REQUIREMENTS.md).

## Files

| File | What it holds |
|---|---|
| [`extraction/shade_response_extraction.csv`](extraction/shade_response_extraction.csv) | 224 treatment rows: 49 from 14 papers, 175 from the Laub et al. (2022) data set |
| [`papers/bibliography.csv`](papers/bibliography.csv) | The 15 sources, with DOI, study type and licence (PDFs stay local) |
| [`papers/SOURCE_laub_2022_shade_metaanalysis.md`](papers/SOURCE_laub_2022_shade_metaanalysis.md) | Source card for the meta-analysis data set (CC BY 4.0) |
| [`parameters/group_curves_laub2022.csv`](parameters/group_curves_laub2022.csv) | `(L_t, k)` per crop type, fitted to the meta-analysis means and 95% CI |
| [`parameters/crop_parameters_draft.csv`](parameters/crop_parameters_draft.csv) | Draft `(L_t, k)` low / central / high and grade for each research crop |

Scripts: `_scripts/build_shade_extraction.py`, then `_scripts/fit_shade_parameters.py`.

## Method (draft)

- **Light** is the season-mean fraction reaching the crop relative to open field (`L_s` in the model), the same
  quantity the app's physics computes. Each row records how it was obtained in `light_basis`:
  - `measured_season`: measured under the treatment over the season (IARI wheat, Heggelbach, Japan).
  - `measured_range` / `measured_spot` / `measured_window`: a measured range (midpoint used), a spot reading, or
    light during a shading window only (Nanjing cotton, shaded from flowering to boll opening).
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
- **Single-study curves.** Cotton and mustard have no meta-analysis group, so each is fitted to its own study
  (at least 3 points spanning 0.15 of light), with an *assumed* spread: threshold ±0.05, slope ±25%.
- **Secondary values.** Six APV trials (Anand wheat, French maize, two Japanese rice trials, Nigerian moong,
  Brazilian sugarcane) are paywalled or were not read in full. Their values come from the study table of a 2026
  systematic review (*Energies* 19(2):539, doi:10.3390/en19020539) or the paper's abstract, and each row says so.
  Read the primary papers before treating these as final.
- **Grades** follow spec §13.3. A crop with no group curve and too few points to fit gets D.

## Draft parameters

| Crop | Grade | L_t central | k central | Basis | Indian evidence |
|---|---|---|---|---|---|
| Rice | B | 0.96 | 1.06 | C3 cereal group; three APV trials (Korea, Shonai and Chikusei in Japan) give 0.77–0.91 at 0.68–0.75 light | none yet |
| Wheat | **A** | 0.89 | 1.18 | Own fit, 49 points, 13 studies | IARI Delhi shade nets; Anand (Gujarat) APV |
| Soybean | B | 1.00 | 1.18 | Own fit, 56 points, 10 studies | IARI shade nets (in meta-analysis) |
| Cotton | C | 1.00 | 0.84 | Own fit to one study (Nanjing, nets from flowering to boll opening): 81–84% at 0.79 light, 67–70% at 0.62 | none |
| Maize | B | 1.00 | 1.20 | Own fit, 54 points, 11 studies (adds French APV) | none |
| Gram (chickpea) | B | 1.00 | 1.22 | Grain-legume group; the CAZRI point sits 0.21 above it | CAZRI Jodhpur APV |
| Mustard | B | 0.73 | 3.00 | Own fit to one study (CAFRI Jhansi net houses): 80% at 0.64 light, 16% at 0.47, 10% at 0.25 | CAFRI Jhansi |
| Bajra | C | 1.00 | 1.32 | Maize (C4) group, borrowed | none |
| Sugarcane | **D** | — | — | The one APV trial (Brazil) shows a 39% *gain* at 0.65–0.70 light; not usable for a loss curve | none |
| Moong | B | 1.00 | 1.22 | Grain-legume group; CAZRI sits 0.06 above it; Nigerian APV gives 1.23 at 0.88 and 0.81 at 0.85 light | CAZRI Jodhpur APV |
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

**Against the spec targets (§7.3):** the top 10 crops should be grade B or better, and 7 are (wheat at A; rice,
soybean, maize, gram, mustard and moong at B). Cotton and bajra are C and sugarcane is D. The other 10 crops should be
grade C or better; sesame and cumin are still D.

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
5. **Mustard has a sharp threshold.** At Jhansi, mustard kept 80% of yield at 64% light but collapsed to 16% at
   47%. The authors put the critical limit at about 67% light. The fitted curve (`L_t` 0.73, slope 3.0) is far
   steeper than any meta-analysis group. Caveats: per-plant yields read from a chart, and net houses rather than
   open field.
6. **Cotton loses moderately, but only the boll-forming window was shaded.** At Nanjing, nets from flowering to
   boll opening cost 16–19% of lint at 21% shade and 30–33% at 38% shade. Averaged over the whole season the
   light cut was much smaller, so per unit of season-mean light cotton may be more sensitive than this curve says.
7. **Sugarcane may gain from partial shade.** The one APV trial (Alagoas, Brazil) got 82 against 59 t/ha of
   stalk at 65–70% light, with a higher leaf area index. One site and one season; the cause (light, heat or
   water) is not isolated. It stays out of the fit until there is a second trial.
8. **Year-to-year swings are large.** The same APV gave +3% and −19% for wheat and +11% and −18% for potato in
   Germany (dry vs wet years), and Korea's soybean fell to 31% in a very wet year. The low–high range has to
   carry this.

## Next research, in priority order

1. **Sugarcane** (top-10 crop at D): any shade, intercrop or APV trial reporting cane yield against light, ideally
   from India (IISR Lucknow, VSI Pune, SBI Coimbatore).
2. **Cotton and bajra up to B**: a second cotton study, ideally season-long or Indian (CICR Nagpur, agroforestry
   trials); any bajra shade or intercrop trial (ICRISAT, CAZRI, AICRP on pearl millet).
3. **Read the paywalled primaries** behind the review-sourced rows (Anand wheat above all, since it makes wheat
   grade A), and get Indian rice data (NRRI Cuttack low-light trials; KrishiKosh theses).
4. **Jowar** shade or intercrop trials (ICRISAT, AICRP), to replace the borrowed maize curve.
5. **Sesame and cumin** (still D), then lentil, groundnut, onion and potato, from Indian or tropical trials.
6. **Confirm the CAZRI layout and light.** CAZRI's light-map paper (Santra, Meena and Yadav 2021, *Biosystems
   Engineering*, doi:10.1016/j.biosystemseng.2021.06.017) maps daily light for the same plant: 0–5 mol/m²/day
   below the panels, 5–20 in partly shaded and 20–30 in unshaded interspace. It is paywalled, and ICAR's repository
   (krishi.icar.gov.in) could not be reached from here. If you can get the PDF, its edge height and light maps would
   replace the modelled values. For Raichur, find measured light under its nets (the authors' thesis on KrishiKosh).
7. **Freeze a hold-out set** for validation (D17) once there are at least 30 Indian points across 8 crops. The
   `used_for` column is "unassigned" until then.

The ICAR-CAZRI programme is the strongest Indian lead. Its other papers (Santra et al. 2017, 2018 and 2020; Poonia
et al. 2021 in *Indian Farmer*) may hold more crop-by-design yields.
