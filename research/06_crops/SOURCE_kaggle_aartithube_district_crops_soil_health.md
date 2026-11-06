# SOURCE: Geo-Referenced Crop Prediction dataset (Kaggle, aartithube): district major crops + Soil Health Card NPK/pH shares

| Field | Value |
|---|---|
| Dataset ID | D10 (major crops per district, a cross-check only), D04 (soil nutrient status) |
| Publisher / owner | Kaggle user "aartithube" (compiler). Soil data: Government of India Soil Health Card portal (soilhealth.dac.gov.in), 2024–25 analysis reports |
| Dataset name and version | `aartithube/geo-referenced-crop-prediction-dataset`, file `CropDataset-Enhanced.csv`, "updated a year ago" (≈ 2025) |
| URL / access route | https://www.kaggle.com/datasets/aartithube/geo-referenced-crop-prediction-dataset. Downloaded from `https://www.kaggle.com/api/v1/datasets/download/aartithube/geo-referenced-crop-prediction-dataset` (public) |
| Accessed on (YYYY-MM-DD) | 2026-11-06 |
| Reference year(s) covered | Soil Health Card reports 2024–25. The crop lists are undated, compiled by the author |
| Spatial coverage | All-India, 730 district rows |
| Spatial unit or resolution | District (name only, no LGD code), plus a geocoded point (approximate locality / admin centroid) |
| Temporal resolution | One-off |
| Licence | Kaggle "Other (specified in description)": compiled from public Soil Health Portal data; **the author asks for non-commercial, academic or research use only**, crediting soilhealth.dac.gov.in and the author |
| OK for a public open-source app? | **Restricted (non-commercial).** Keep it local; do not commit or ship it. Re-derive the soil shares directly from the Soil Health Card portal if the app needs them |
| Required attribution text | "Soil nutrient status: Soil Health Card portal, DA&FW (soilhealth.dac.gov.in); compiled by aartithube (Kaggle)" |
| Citation | aartithube (2025). Geo-Referenced Crop Prediction dataset [dataset]. Kaggle. https://www.kaggle.com/datasets/aartithube/geo-referenced-crop-prediction-dataset |
| Files in this folder | Git-ignored: `area_production_yield/raw/kaggle_aartithube/CropDataset-Enhanced.csv` (179 KB). The archive also held a Flask app, a notebook and pickled ML models (`*.pkl`); they were **deleted unopened**, because pickles can execute code when loaded and they are not needed |
| Units and key column meanings | `Address`, `Formatted address`, `Region` (state), `Latitude`, `Longitude` (geocoder output, WGS84), `Status geocode` (90% "Ok"; ~8% ambiguous "2 found"), `Crop` (free-text, comma-separated list of "famous, suitable and recommended" crops). `Nitrogen/Phosphorous/Potassium - High/Medium/Low` and `pH - Acidic/Neutral/Alkaline`: share of soil samples in each class (% strings) |
| Known caveats and gaps | (1) Crop lists are free text with inconsistent spelling ("soyabean", "Soybean"), so they are **not area-weighted**: use UPAg APY (D10) for real crop shares and this only as a sanity check. (2) Geocodes are approximate, and ~8% are ambiguous. (3) District names follow the Soil Health Card portal, so map them to LGD via the D00 alias table. (4) Percent fields are strings with `%` |
| Processing notes | None yet |
