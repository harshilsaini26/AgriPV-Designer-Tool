# D16 crop shade response: evidence status (draft, 2026-11-14)

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

- **Light** is the fraction reaching the crop relative to open field (`L_s` in the model). Where a paper gives only
  a shade-net rating or panel cover ratio, light = 1 − that value, and the row says so in `light_method`.
- **Group curves** come from the meta-analysis predictions (Table S2) for each crop type, fitted over light
  0.4–0.95. Central uses the mean, low uses the lower 95% bound and high the upper bound.
- **Crop curves** replace the group curve only where a crop has at least 8 points from 3 studies covering 0.3 of the
  light range (wheat, soybean and maize so far). They keep the group's low–high spread.
- **Grades** follow spec §13.3. A crop with no group curve and too few points to fit gets D.

## Draft parameters

| Crop | Grade | L_t central | k central | Basis | Indian evidence |
|---|---|---|---|---|---|
| Rice | C | 0.96 | 1.06 | C3 cereal group; Korea APV checks it (0.81 and 0.91 at about 30% shade) | none yet |
| Wheat | B | 0.88 | 1.30 | Own fit, 47 points, 12 studies | IARI Delhi shade nets |
| Soybean | B | 1.00 | 1.18 | Own fit, 56 points, 10 studies | IARI shade nets (in meta-analysis) |
| Cotton | **D** | — | — | No data, no close group | none |
| Maize | B | 1.00 | 1.24 | Own fit, 51 points, 10 studies | none |
| Gram (chickpea) | B | 1.00 | 1.22 | Grain-legume group | CAZRI Jodhpur APV |
| Mustard | **D** | — | — | No data, no close group | none |
| Bajra | C | 1.00 | 1.32 | Maize (C4) group, borrowed | none |
| Sugarcane | **D** | — | — | No data, no close group | none |
| Moong | B | 1.00 | 1.22 | Grain-legume group | CAZRI Jodhpur APV |
| Groundnut | C | 1.00 | 1.22 | Grain-legume group | none |
| Tur | B | 1.00 | 1.22 | Grain-legume group | Raichur shade nets |
| Jowar | C | 1.00 | 1.32 | Maize (C4) group, borrowed | none |
| Urad | B | 1.00 | 1.22 | Grain-legume group | Raichur shade nets |
| Guar | C | 1.00 | 1.22 | Grain-legume group | CAZRI (yield only, no light value) |
| Potato | B | 0.96 | 1.10 | Tuber group | none |
| Onion | C | 0.96 | 1.10 | Tuber group, borrowed for a bulb crop | none |
| Lentil | C | 1.00 | 1.22 | Grain-legume group | none |
| Sesame | **D** | — | — | No data, no close group | none |
| Cumin | **D** | — | — | One CAZRI point, no group to anchor it | CAZRI Jodhpur APV |

**Against the spec targets (§7.3):** the top 10 crops should be grade B or better, but only 5 are (wheat, soybean,
maize, gram, moong). Cotton, mustard and sugarcane are D, and rice and bajra are C. The other 10 crops should be grade C or better;
sesame and cumin are D.

## What the evidence says so far

1. **The meta-analysis curves are steep.** Grain legumes and maize lose yield from the first bit of shade (`L_t` = 1);
   C3 cereals and potato hold to about 4% shade. At 70% light the curves give about 72% (C3 cereals), 63%
   (grain legumes) and 61% (maize).
2. **Indian trials lose far less than those curves predict.** At CAZRI Jodhpur, chickpea kept 93% of yield and
   cumin 89% where spot PAR was 47% and 57% of open field. At Raichur, tur kept about 80% under nets rated 50% and
   75%. Two reasons are likely, and they need separating before any refit:
   - **The light numbers are not like for like.** CAZRI's values are midday PAR in the shaded part of the
     interspace, so the daily light over the whole cropped strip is higher. Net ratings (Raichur) often overstate
     the real cut: Raichur's 75% net gave the same yield as its 50% net.
   - **India's high sunlight.** Crops in Jodhpur and Raichur sit nearer light saturation than in the mostly
     temperate meta-analysis studies, so they can lose some light at a smaller cost.
3. **Indian wheat is the exception.** Under IARI's shade nets in Delhi, wheat dropped to 66–78% of yield at 20%
   shade, worse than the meta-analysis C3 curve. The winter crop grows in lower light (fog, short days), which may explain it.
4. **Year-to-year swings are large.** The same APV gave +3% and −19% for wheat and +11% and −18% for potato in
   Germany (dry vs wet years), and Korea's soybean fell to 31% in a very wet year. The low–high range has to
   carry this.

## Next research, in priority order

1. **Fix the light metric for the Indian trials.** CAZRI published light (PPFD) maps of its system in space and
   time (Santra, Meena and Yadav 2021, *Biosystems Engineering*; cited in Poonia and Santra 2024). Use them to convert the spot PAR values to daily light over
   the cropped strip, then refit the legumes and cumin.
2. **Cotton, mustard and sugarcane** (top-10 crops at D). Look for season-long shade-net or agroforestry trials
   (cotton under shade in China and India; mustard under poplar or shade nets in Punjab, Haryana and Jhansi;
   sugarcane intercropped or under shade in Brazil and India) and any APV trials.
3. **Rice from India** (NRRI Cuttack low-light trials; KrishiKosh theses), plus the six-year Japanese APV trial
   (Chikusei 2018–2023, *Field Crops Research*, 23% loss at 27% panel cover; DOI to confirm).
4. **Bajra and jowar** shade or intercrop trials (ICRISAT, AICRP), to replace the borrowed maize curve.
5. **Sesame, lentil, groundnut, onion and potato** from Indian or tropical trials.
6. **Freeze a hold-out set** for validation (D17) once there are at least 30 Indian points across 8 crops. The
   `used_for` column is "unassigned" until then.

The ICAR-CAZRI programme is the strongest Indian lead. Its other papers (Santra et al. 2017, 2018 and 2020; Poonia
et al. 2021 in *Indian Farmer*) may hold more crop-by-design yields.
