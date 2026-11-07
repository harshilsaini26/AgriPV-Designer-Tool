# SOURCE: ISRIC SoilGrids 2.0: district topsoil (0–30 cm) properties

| Field | Value |
|---|---|
| Dataset ID | D04 (primary soil source) |
| Publisher / owner | ISRIC – World Soil Information (Wageningen, NL) |
| Dataset name and version | SoilGrids 2.0 (`soilgrids/latest`), **1 km aggregated mean** layers (resampled by ISRIC from the 250 m means) |
| URL / access route | `https://files.isric.org/soilgrids/latest/data_aggregated/1000m/<prop>/<prop>_<depth>_mean_1000.tif` (global tiled GeoTIFF, Goode Homolosine ESRI:54052, int16, nodata −32768; ≈ 190 MB each). Only the India window is read, over HTTP range requests. 250 m originals: `…/latest/data/<prop>/` (VRT plus tiles); also on Google Earth Engine (`projects/soilgrids-isric/*`) |
| Accessed on (YYYY-MM-DD) | 2026-11-07 |
| Reference year(s) covered | Model release 2020; built from WoSIS profiles spanning decades (no single reference year) |
| Spatial coverage | India window 66.5–98° E, 6–38° N |
| Spatial unit or resolution | 1 km (aggregated). About 1,000–10,000+ cells per district |
| Temporal resolution | Static |
| Licence | **CC BY 4.0**: "The SoilGrids maps are publicly available under the CC-BY 4.0 License" (ISRIC `data_aggregated/README.md`, checked 2026-11-07) |
| OK for a public open-source app? | **OK** with attribution |
| Required attribution text | "Soil properties derived from ISRIC SoilGrids 2.0 (https://soilgrids.org), CC BY 4.0. Poggio et al. (2021)" |
| Citation | Poggio, L. et al. (2021). SoilGrids 2.0: producing soil information for the globe with quantified spatial uncertainty. *SOIL* 7, 217–240. https://doi.org/10.5194/soil-7-217-2021 |
| Files in this folder | Committed: `soilgrids_v2_district_topsoil_0-30cm.csv` (785 LGD districts). Git-ignored: `raw/soilgrids_v2_1km/<prop>_<depth>.tif` (India clips, 21 files) and `<prop>_0-30cm_weighted.tif` |
| Units and key column meanings | 0–30 cm thickness-weighted means, i.e. (5·[0–5] + 10·[5–15] + 15·[15–30]) / 30, in conventional units: `clay_pct`, `silt_pct`, `sand_pct` (%), `ph_h2o` (pH in water), `soc_g_per_kg` (soil organic carbon, g/kg; ÷ 10 = % OC), `bulk_density_g_cm3`, `cec_cmolc_per_kg` (cation exchange capacity at pH 7); `n_cells_1km` (coverage-weighted cell count); `texture_sum_pct` (check ≈ 100); `weighting` |
| Known caveats and gaps | (1) **Area-weighted, not cropland-weighted** yet. (2) The 1 km layers are averages of 250 m predictions; fine for district means. (3) **No soil depth and no soil class (order) in v2.0**: depth to bedrock (`BDTICM`) and USDA suborder (`TAXOUSDA`) exist only in SoilGrids 2017, licensed **ODbL** (share-alike for derived databases), so keep any derived table under ODbL; see `SOURCE_CANDIDATES.md`. (4) The models explain about 30–70% of soil variation; use for regional context, not field design. (5) Soil Health Card nutrient data (N, P, K, micronutrients) is a separate, plot-based source with no bulk download |
| Processing notes | `research/_scripts/soilgrids_district_topsoil.py` (rasterio window clips; `exactextract` coverage-weighted district means with polygons reprojected to ESRI:54052; joins on a row key because two PoK polygons share LGD code 0). Run 2026-11-07: 784/785 districts; **Mumbai** has no value because SoilGrids masks built-up land. Clay + silt + sand = 100% everywhere. Ranges (district medians): clay 18–48% (31), sand 8–58% (36), pH 5.0–8.8 (6.9), SOC 3.6–57 g/kg (13), bulk density 1.04–1.68 g/cm³, CEC 9–49 cmol(c)/kg. Spot checks behave as expected: black-soil Vidarbha / Malwa (Nagpur 46% clay, CEC 48; Akola 44%, 42), sandy alkaline Jaisalmer (58% sand, pH 8.0, SOC 3.6 g/kg), acidic high-carbon Khasi Hills (pH 5.2, SOC 34 g/kg) |
