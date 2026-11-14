# D16 crop shade response: evidence status (draft, updated 2026-11-14)

How far the shade-response evidence goes for the 20 research crops, what the first parameters are, and what to
find next. The model curve and grades are in the product spec (§12, §13); the requirements are in
[`DATA_REQUIREMENTS.md` (D16)](../DATA_REQUIREMENTS.md).

## Files

| File | What it holds |
|---|---|
| [`extraction/shade_response_extraction.csv`](extraction/shade_response_extraction.csv) | 252 treatment rows: 77 from 18 papers, 175 from the Laub et al. (2022) data set |
| [`papers/bibliography.csv`](papers/bibliography.csv) | The 19 sources, with DOI, study type and licence (PDFs stay local) |
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
  - `net_rating`: a shade-net rating whose yields fall steadily with shade (Raichur 2023 oilseeds). Used, but
    flagged.
  - `nominal_net_inconsistent`: a net rating that the yields show is wrong (Raichur 2021 pulses). **Excluded from
    fitting.**
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
- **Own curves without a group.** Cotton (2 studies), sesame (2 studies) and mustard (1 study) have no
  meta-analysis group, so each is fitted to its own points (at least 3 spanning 0.10 of light), with an *assumed*
  spread: threshold ±0.05, slope ±25%. The fit searches thresholds 0.40–1.00 and slopes 0–6.
- **Sugarcane** borrows the maize (C4) group curve. Sugarcane, maize and sorghum are C4 grasses of the same tribe
  (Andropogoneae), which spec §13.3 allows as an extension from a closely related crop (grade C).
- **Secondary values.** Six APV trials (Anand wheat, French maize, two Japanese rice trials, Nigerian moong,
  Brazilian sugarcane) are paywalled or were not read in full. Their values come from the study table of a 2026
  systematic review (*Energies* 19(2):539, doi:10.3390/en19020539) or the paper's abstract, and each row says so.
  Read the primary papers before treating these as final.
- **Grades** follow spec §13.3. A crop with no group curve and too few points to fit gets D.

## Draft parameters

| Crop | Grade | L_t central | k central | Basis | Indian evidence |
|---|---|---|---|---|---|
| Rice | B | 0.96 | 1.06 | C3 cereal group; APV trials at four Korean farms and two Japanese sites give 0.70–0.91 at 0.68–0.75 light | none yet |
| Wheat | **A** | 0.89 | 1.18 | Own fit, 49 points, 13 studies | IARI Delhi shade nets; Anand (Gujarat) APV |
| Soybean | **A** | 1.00 | 1.10 | Own fit, 63 points, 13 studies | IARI shade nets (in meta-analysis); Raichur 2023 nets |
| Cotton | B | 1.00 | 0.80 | Own fit to two studies, both shaded only from flowering: Nanjing (81–84% at 0.79 light, 67–70% at 0.62) and Pettigrew 1994, USA (80% at 0.70) | none |
| Maize | B | 1.00 | 1.18 | Own fit, 57 points, 12 studies (adds French and Korean APV) | none |
| Gram (chickpea) | B | 1.00 | 1.22 | Grain-legume group; the CAZRI point sits 0.21 above it | CAZRI Jodhpur APV |
| Mustard | B | 0.70 | 3.60 | Own fit to one study (CAFRI Jhansi net houses): 80% at 0.64 light, 16% at 0.47, 10% at 0.25 | CAFRI Jhansi |
| Bajra | C | 1.00 | 1.32 | Maize (C4) group, borrowed; no direct pearl millet trial found | none |
| Sugarcane | C | 1.00 | 1.32 | Maize (C4) group, borrowed; conflicts with the one APV trial (Brazil, 39% *gain* at 0.65–0.70 light) | none |
| Moong | B | 1.00 | 1.22 | Grain-legume group; CAZRI sits 0.06 above it; Nigerian APV (1.23 at 0.88, 0.81 at 0.85) and Korean APV (0.79 at 0.79, 0.56 at 0.74 and 0.68) | CAZRI Jodhpur APV |
| Groundnut | B | 1.00 | 1.22 | Grain-legume group; Raichur 2023 sits above it (75% at 0.70 light, 50% at 0.40) | Raichur 2023 shade nets |
| Tur | C | 1.00 | 1.22 | Grain-legume group | Raichur shade nets (excluded: light unreliable) |
| Jowar | C | 1.00 | 1.32 | Maize (C4) group, borrowed | none |
| Urad | C | 1.00 | 1.22 | Grain-legume group | Raichur shade nets (excluded: light unreliable) |
| Guar | B | 1.00 | 1.22 | Grain-legume group; the CAZRI point sits on it | CAZRI Jodhpur APV |
| Potato | B | 1.00 | 0.68 | Own fit, 11 points, 3 studies (Germany, Korea, meta-analysis); gentler than the tuber group | none |
| Onion | C | 0.96 | 1.10 | Tuber group, borrowed for a bulb crop | none |
| Lentil | C | 1.00 | 1.22 | Grain-legume group | none |
| Sesame | B | 0.80 | 3.02 | Own fit to two Korean APV studies: 93% at 0.79 light, 87% at 0.74, 81% and 47% at 0.68; fitted only over 0.68–0.79 light | none |
| Cumin | **D** | — | — | One CAZRI point (89% at 0.77 light), no group to anchor a curve | CAZRI Jodhpur APV |

**Against the spec targets (§7.3):** the top 10 crops should be grade B or better, and 8 are (wheat and soybean
at A; rice, cotton, maize, gram, mustard and moong at B). Bajra and sugarcane are C, both on the borrowed maize
curve. The other 10 crops should be grade C or better, and all are except cumin (D).

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
   47%. The authors put the critical limit at about 67% light. The fitted curve (`L_t` 0.70, slope 3.6) is far
   steeper than any meta-analysis group. Caveats: per-plant yields read from a chart, and net houses rather than
   open field.
6. **Cotton loses moderately, but only the boll-forming window was shaded.** At Nanjing, nets from flowering to
   boll opening cost 16–19% of lint at 21% shade and 30–33% at 38% shade; Pettigrew's 30% shade over reproductive
   development cost 20% (USA). Their slopes are 0.65–0.86 per unit of light. Averaged over the whole season the light cut was
   smaller, so per unit of season-mean light cotton may be more sensitive than this curve says.
7. **Sugarcane evidence conflicts.** The one APV trial (Alagoas, Brazil) got 82 against 59 t/ha of stalk at
   65–70% light, with a higher leaf area index. One site and one season; the cause (light, heat or water) is not
   isolated. Under tung trees in southern Brazil (Schwerz et al. 2018, *Anais da Academia Brasileira de Ciências*
   90(4), doi:10.1590/0001-3765201820160806), cane lost 17.5% and 32.7% in the wide and narrow tree spacings. That
   study did not measure light relative to open field, and tree roots compete too, so it is not in the table. The
   borrowed maize curve is a cautious default until an Indian trial exists.
8. **Indian kharif shade-net trials sit above the curves.** At Raichur in 2023, groundnut kept 75% and 50% of yield
   under nets rated 30% and 60%, and soybean 79% and 64%; the curves give about 63% and 27% (groundnut) and 67%
   and 34% (soybean). Either the net ratings overstate the real cut (as at Raichur in 2021), or high-sunlight
   kharif crops lose less per unit of shade. Measured light under the nets would settle it.
9. **Sesame also has a threshold, around 68–75% light.** In Jeollanam-do (Korea) sesame kept 93% and 87% of yield
   under APV covering 21% and 26% of the field, then fell to 47% at 32% cover; at another Korean farm (Goesan) it kept
   81% at 32% cover. The fitted curve (`L_t` 0.80, slope 3.0) only covers 0.68–0.79 light; below that it is an
   extrapolation, and the low and high bounds are assumed, not measured.
10. **No direct bajra evidence yet.** No shade-net, intercrop or APV trial reporting pearl millet grain yield against
    light turned up. Two leads were not usable: a foxtail millet trial (Photosynthetica 2017) shaded only 15 days of
    grain filling, and the University of Illinois APV sorghum trial (Smart Agricultural Technology 2025,
    doi:10.1016/j.atech.2025.101647), whose page asked for a CAPTCHA. That paper reports that sorghum offsets
    fewer grains with heavier grains, with no yield penalty in the least-shaded row, which suggests C4 cereals may
    lose less than the maize curve says.
11. **Year-to-year swings are large.** The same APV gave +3% and −19% for wheat and +11% and −18% for potato in
   Germany (dry vs wet years), and Korea's soybean fell to 31% in a very wet year. The low–high range has to
   carry this.

## Next research, in priority order

1. **Bajra and sugarcane up to B** (the last two top-10 crops at C). Bajra: any shade-net, intercrop or APV trial
   with measured light (ICRISAT, CAZRI, AICRP on pearl millet); also read the Illinois APV sorghum paper (open
   access, but behind a CAPTCHA here), which would support jowar directly. Sugarcane: an Indian trial reporting
   cane yield against light (IISR Lucknow, VSI Pune, SBI Coimbatore), and the full Brazilian APV paper to see why
   cane gained.
2. **Measured light under Indian shade nets.** Raichur's two trials disagree with each other and sit above the
   curves; the authors' theses (UAS Raichur, KrishiKosh) may have the PAR readings.
3. **Read the paywalled primaries** behind the review-sourced rows (Anand wheat above all, since it makes wheat
   grade A), and get Indian rice data (NRRI Cuttack low-light trials; KrishiKosh theses).
4. **Cumin** (still D), then Indian or tropical trials for sesame (to extend its curve below 0.68 light), jowar,
   tur, urad, lentil and onion.
5. **Confirm the CAZRI layout and light.** CAZRI's light-map paper (Santra, Meena and Yadav 2021, *Biosystems
   Engineering*, doi:10.1016/j.biosystemseng.2021.06.017) maps daily light for the same plant: 0–5 mol/m²/day
   below the panels, 5–20 in partly shaded and 20–30 in unshaded interspace. It is paywalled, and ICAR's repository
   (krishi.icar.gov.in) could not be reached from here. If you can get the PDF, its edge height and light maps would
   replace the modelled values. For Raichur, find measured light under its nets (the authors' thesis on KrishiKosh).
6. **Freeze a hold-out set** for validation (D17) once there are at least 30 Indian points across 8 crops. The
   `used_for` column is "unassigned" until then.

The ICAR-CAZRI programme is the strongest Indian lead. Its other papers (Santra et al. 2017, 2018 and 2020; Poonia
et al. 2021 in *Indian Farmer*) may hold more crop-by-design yields.
