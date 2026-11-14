"""Build the D16 shade-response extraction table (one row per treatment) and the bibliography.

Usage: uv run --no-project --with openpyxl python -I build_shade_extraction.py <research_dir>

Two inputs:
1. STUDIES / ROWS below: treatments read by hand from the full text of each paper (values as printed; derived
   values are marked in `caveats`).
2. The Laub et al. (2022) meta-analysis data set (ESM 2, CC BY 4.0), kept local at
   09_crop_shade_response/papers/raw/laub_2022_esm2.xlsx. Only crops on, or standing in for, the AgriPV Lab
   research list are kept. Laub reports "reduction in solar radiation" (RSR, %) and yield as % of the unshaded
   control, so light_fraction = 1 - RSR/100 and relative_yield = yield/100.

`light_fraction` is the light reaching the crop relative to open field (the model's L_s). Where a paper only gives a
nominal shade level (net rating, panel cover ratio), light_fraction = 1 - shade and light_method says so.
Writes extraction/shade_response_extraction.csv and papers/bibliography.csv.
"""

import csv
import sys
from pathlib import Path

import openpyxl

REVIEW = (
    "values as tabulated in the systematic review in Energies 19(2):539 (2026), doi:10.3390/en19020539; "
    "primary paper not read (paywalled)"
)

COLS = [
    "study_id",
    "citation",
    "doi_url",
    "peer_reviewed",
    "country",
    "state_region",
    "latitude",
    "longitude",
    "koppen",
    "crop",
    "variety",
    "season",
    "years",
    "irrigated_or_rainfed",
    "shading_method",
    "structure_type",
    "clearance_m",
    "gcr_or_row_spacing",
    "module_type",
    "shade_level_pct",
    "light_fraction",
    "light_measure",
    "light_method",
    "light_basis",
    "control_yield",
    "treatment_yield",
    "yield_unit",
    "relative_yield",
    "sd_or_se",
    "n",
    "quality_notes",
    "water_notes",
    "caveats",
    "used_for",
]

STUDIES = {
    "poonia2024": {
        "citation": "Poonia, S., Santra, P. (2024). Evaluation of agrivoltaic system in Thar Desert of India. "
        "AgriVoltaics Conference Proceedings 1 (AgriVoltaics World Conference 2022)",
        "doi_url": "https://doi.org/10.52825/agripv.v1i.601",
        "peer_reviewed": "Y",
        "country": "India",
        "state_region": "Rajasthan, Jodhpur (ICAR-CAZRI)",
        "latitude": 26.25,
        "longitude": 73.02,
        "koppen": "BWh",
        "study_type": "APV field trial (India)",
        "licence": "CC BY 4.0",
    },
    "jo2022": {
        "citation": "Jo, H., Asekova, S., Bayat, M.A., Ali, L., Song, J.T., Ha, Y.-S., Hong, D.-H., Lee, J.-D. (2022). "
        "Comparison of yield and yield components of several crops grown under agro-photovoltaic system in Korea. "
        "Agriculture 12(5), 619",
        "doi_url": "https://doi.org/10.3390/agriculture12050619",
        "peer_reviewed": "Y",
        "country": "South Korea",
        "state_region": "Gyeongsangbuk-do (Kyungpook National University farm)",
        "latitude": 36.23,
        "longitude": "",  # paper prints 128°78′ E, not a valid value
        "koppen": "Cwa",
        "study_type": "APV field trial (international)",
        "licence": "CC BY 4.0",
    },
    "gonocruz2021": {
        "citation": "Gonocruz, R.A., Nakamura, R., Yoshino, K., Homma, M., Doi, T., Yoshida, Y., Tani, A. (2021). "
        "Analysis of the rice yield under an agrivoltaic system: a case study in Japan. Environments 8(7), 65",
        "doi_url": "https://doi.org/10.3390/environments8070065",
        "peer_reviewed": "Y",
        "country": "Japan",
        "state_region": "Several farms (Farm A–D)",
        "latitude": "",
        "longitude": "",
        "koppen": "Cfa",
        "study_type": "APV field trial with dummy panels (international)",
        "licence": "CC BY 4.0",
    },
    "weselek2021": {
        "citation": "Weselek, A., Bauerle, A., Hartung, J., Zikeli, S., Lewandowski, I., Högy, P. (2021). Agrivoltaic "
        "system impacts on microclimate and yield of different crops within an organic crop rotation in a temperate "
        "climate. Agronomy for Sustainable Development 41, 59",
        "doi_url": "https://doi.org/10.1007/s13593-021-00714-y",
        "peer_reviewed": "Y",
        "country": "Germany",
        "state_region": "Baden-Württemberg, Heggelbach",
        "latitude": 47.86,
        "longitude": 9.10,
        "koppen": "Cfb",
        "study_type": "APV field trial (international, temperate)",
        "licence": "CC BY 4.0",
    },
    "manoj2021": {
        "citation": "Manoj, K.N., Umesh, M.R., Ananda, N., Duttarganvi, S. (2021). Effects of low light intensity on "
        "radiation use efficiency and productivity of tropical pulses. Journal of Agrometeorology 23(3)",
        "doi_url": "https://doi.org/10.54386/jam.v23i3.19",
        "peer_reviewed": "Y",
        "country": "India",
        "state_region": "Karnataka, Raichur (UAS Raichur)",
        "latitude": 16.2,
        "longitude": 77.32,
        "koppen": "BSh",
        "study_type": "Shade-net field trial (India)",
        "licence": "open access (journal)",
    },
    "mukherjee2020": {
        "citation": "Mukherjee, J., Yadav, B., Sehgal, V.K., Krishnan, P., Dhakar, R.K. (2020). Radiation dimming "
        "induced modifications in radiation utilization of wheat (Triticum aestivum) crop. Journal of "
        "Agrometeorology 22(3)",
        "doi_url": "https://doi.org/10.54386/jam.v22i3.294",
        "peer_reviewed": "Y",
        "country": "India",
        "state_region": "Delhi (ICAR-IARI farm)",
        "latitude": 28.62,
        "longitude": 77.15,
        "koppen": "BSh",
        "study_type": "Shade-net field trial (India)",
        "licence": "open access (journal)",
    },
    "chen2017": {
        "citation": "Chen, B.L., Yang, H.K., Ma, Y.N., Liu, J.R., Lv, F.J., Chen, J., Meng, Y.L., Wang, Y.H., Zhou, Z.G. "
        "(2017). Effect of shading on yield, fiber quality and physiological characteristics of cotton subtending "
        "leaves on different fruiting positions. Photosynthetica 55(2), 240-250",
        "doi_url": "https://doi.org/10.1007/s11099-016-0209-7",
        "peer_reviewed": "Y",
        "country": "China",
        "state_region": "Jiangsu, Nanjing",
        "latitude": 32.0,
        "longitude": 118.8,
        "koppen": "Cfa",
        "study_type": "Shade-net field trial (international)",
        "licence": "journal article (facts extracted)",
    },
    "alam2018": {
        "citation": "Alam, B., Singh, R., Chaturvedi, M., Newaj, R., Chaturvedi, O.P. (2018). Determination of "
        "critical low light limit and adaptive physiological and biochemical traits regulating growth and yield of "
        "mustard (Brassica juncea Coss.). Physiology and Molecular Biology of Plants 24(5), 985 ff.",
        "doi_url": "https://doi.org/10.1007/s12298-018-0537-0",
        "peer_reviewed": "Y",
        "country": "India",
        "state_region": "Uttar Pradesh, Jhansi (ICAR-CAFRI)",
        "latitude": 25.45,
        "longitude": 78.58,
        "koppen": "BSh",
        "study_type": "Shade-net house trial (India)",
        "licence": "journal article (facts extracted; full text in PMC)",
    },
    "prakash2025": {
        "citation": "Prakash, V., Lunagaria, M., Upadhyaya, A., Das, A., Gupta, A., Kumar, Y., Subash, N., Ghasal, P., "
        "Singh, A., Trivedi, A., et al. (2025). Influence of agrivoltaic system-induced microclimate modifications "
        "on wheat growth and yield. Agricultural and Forest Meteorology 373, 110775",
        "doi_url": "https://doi.org/10.1016/j.agrformet.2025.110775",
        "peer_reviewed": "Y",
        "country": "India",
        "state_region": "Gujarat, Anand",
        "latitude": 22.56,
        "longitude": 72.95,
        "koppen": "BSh",
        "study_type": "APV field trial (India)",
        "licence": "journal article (facts extracted)",
    },
    "ramosfuentes2023": {
        "citation": "Ramos-Fuentes, I.A., Elamri, Y., Cheviron, B., Dejean, C., Belaud, G., Fumey, D. (2023). Effects "
        "of shade and deficit irrigation on maize growth and development in fixed and dynamic AgriVoltaic systems. "
        "Agricultural Water Management 280, 108187",
        "doi_url": "https://doi.org/10.1016/j.agwat.2023.108187",
        "peer_reviewed": "Y",
        "country": "France",
        "state_region": "Occitanie",
        "latitude": 43.6,
        "longitude": 3.9,
        "koppen": "Csa",
        "study_type": "APV field trial (international)",
        "licence": "journal article (facts extracted)",
    },
    "nasukawa2025": {
        "citation": "Nasukawa, H., Kuwabara, Y., Tatsumi, K., Tajima, R. (2025). Rice yield and energy balance in an "
        "agrivoltaic system established in Shonai plain, northern Japan. Science of the Total Environment 959, 178315",
        "doi_url": "https://doi.org/10.1016/j.scitotenv.2024.178315",
        "peer_reviewed": "Y",
        "country": "Japan",
        "state_region": "Yamagata, Shonai plain",
        "latitude": 38.9,
        "longitude": 139.85,
        "koppen": "Cfa",
        "study_type": "APV field trial (international)",
        "licence": "journal article (facts extracted)",
    },
    "thum2025": {
        "citation": "Thum, C.H., Okada, K., Yamasaki, Y., Kato, Y. (2025). Impacts of agrivoltaic systems on "
        "microclimate, grain yield, and quality of lowland rice under a temperate climate. Field Crops Research 326, "
        "109877",
        "doi_url": "https://doi.org/10.1016/j.fcr.2025.109877",
        "peer_reviewed": "Y",
        "country": "Japan",
        "state_region": "Ibaraki, Chikusei",
        "latitude": 36.3,
        "longitude": 139.98,
        "koppen": "Cfa",
        "study_type": "APV field trial (international)",
        "licence": "journal article (facts extracted)",
    },
    "ukwu2025": {
        "citation": "Ukwu, U.N., Muller, O., Meier-Gruell, M., Uguru, M.I. (2025). Yield sensitivity of mungbean "
        "(Vigna radiata L.) genotypes to different agrivoltaic environments in tropical Nigeria. Plants 14, 1326",
        "doi_url": "https://doi.org/10.3390/plants14091326",
        "peer_reviewed": "Y",
        "country": "Nigeria",
        "state_region": "Enugu, Nsukka",
        "latitude": 6.86,
        "longitude": 7.4,
        "koppen": "Aw",
        "study_type": "APV field trial (international, tropical)",
        "licence": "CC BY 4.0",
    },
    "junior2025": {
        "citation": "Junior, R.A.F., Torres, I.C., de Souza, L.F.L., dos Santos, M.A., Cavalcante, M.A.A., Tiba, C., "
        "de Souza, J.L. (2025). Agrophotovoltaic systems in sugarcane crop - a Brazilian case study. Energy "
        "Conversion and Management 344, 120307",
        "doi_url": "https://doi.org/10.1016/j.enconman.2025.120307",
        "peer_reviewed": "Y",
        "country": "Brazil",
        "state_region": "Alagoas (Santa Clotilde mill)",
        "latitude": -9.5,
        "longitude": -35.8,
        "koppen": "As",
        "study_type": "APV field trial (international, tropical)",
        "licence": "journal article (facts extracted)",
    },
    "laub2022": {
        "citation": "Laub, M., Pataczek, L., Feuerbacher, A., Zikeli, S., Högy, P. (2022). Contrasting yield responses "
        "at varying levels of shade suggest different suitability of crops for dual land-use systems: a "
        "meta-analysis. Agronomy for Sustainable Development 42, 51 (data set: ESM 2)",
        "doi_url": "https://doi.org/10.1007/s13593-022-00783-7",
        "peer_reviewed": "Y",
        "country": "multiple",
        "state_region": "",
        "latitude": "",
        "longitude": "",
        "koppen": "",
        "study_type": "Meta-analysis (58 temperate / subtropical studies)",
        "licence": "CC BY 4.0",
    },
}

CAZRI = {
    "shading_method": "APV",
    "structure_type": "fixed-tilt ground-mounted arrays (2-row and 3-row), crops in inter-row spaces",
    "module_type": "mono-Si, tilt 26°",
    "light_measure": "global irradiance (modelled)",
    "light_method": "season-mean light over the whole interspace, modelled from the published layout "
    "(_scripts/cazri_interspace_light.py): mean of the 2-row (AVS-3) and 3-row (AVS-4, AVS-5) arrays",
    "light_basis": "modelled_season",
}
KHARIF_L = "light 0.91 (range 0.87-0.94 for lower-edge height 0.5-1.5 m and portrait or landscape modules)"
RABI_L = "light 0.77 (range 0.65-0.86 for lower-edge height 0.5-1.5 m and portrait or landscape modules)"
KOREA = {
    "shading_method": "APV",
    "structure_type": "fixed overhead dummy panels, 3.3 m high, 1.5 m apart, tilt 35°",
    "clearance_m": 3.3,
    "gcr_or_row_spacing": "panel cover ratio 30%",
    "module_type": "dummy panels",
    "shade_level_pct": 30,
    "light_fraction": 0.70,
    "light_measure": "area",
    "light_method": "nominal: 1 - panel shading rate (shaded area / system area); not measured",
    "light_basis": "nominal_cover",
}
WESELEK = {
    "shading_method": "APV",
    "structure_type": "elevated overhead APV (Heggelbach research plant)",
    "module_type": "bifacial glass-glass",
    "shade_level_pct": 30,
    "light_fraction": 0.70,
    "light_measure": "PAR",
    "light_method": "measured: mean daily PAR about 30% lower under AV than reference, both years",
    "light_basis": "measured_season",
}
MANOJ = {
    "shading_method": "shade net",
    "structure_type": "white shade nets from 25 DAS to harvest",
    "light_measure": "nominal",
    "light_basis": "nominal_net_inconsistent",
    "years": "two seasons (mean)",
    "season": "kharif",
    "irrigated_or_rainfed": "rainfed",
    "yield_unit": "kg/ha grain",
}
MUKH = {
    "shading_method": "shade net",
    "structure_type": "shade nets rated 20/35/50/75% over the whole season",
    "light_measure": "global irradiance (measured)",
    "light_method": "mean of the global radiation measured under each net on 8 dates (61-128 DAS), Table 1",
    "light_basis": "measured_season",
    "season": "rabi",
    "irrigated_or_rainfed": "irrigated",
    "yield_unit": "g/m2 grain",
    "variety": "mean of HD 2967, WR 544, PBW 502",
}


def r(sid, **kw):
    row = {c: "" for c in COLS}
    row.update({k: v for k, v in STUDIES[sid].items() if k in COLS})
    row["study_id"] = sid
    row.update(kw)
    if row["relative_yield"] == "" and row["control_yield"] and row["treatment_yield"]:
        row["relative_yield"] = round(float(row["treatment_yield"]) / float(row["control_yield"]), 3)
    if row["shade_level_pct"] == "" and row["light_fraction"] != "":
        row["shade_level_pct"] = round(100 * (1 - float(row["light_fraction"])), 1)
    return row


ROWS = [
    # ICAR-CAZRI Jodhpur, kharif 2021 (rainfed) and rabi 2021-22 (irrigated). Kharif controls are not printed:
    # derived from the AVS mean and the stated % reduction.
    r(
        "poonia2024",
        crop="moong",
        season="kharif",
        years="2021",
        irrigated_or_rainfed="rainfed",
        **CAZRI,
        light_fraction=0.911,
        treatment_yield=1155,
        control_yield=1211,
        yield_unit="kg/ha",
        relative_yield=0.954,
        caveats="control derived (1155 / 0.954); " + KHARIF_L + "; paper's spot midday PAR in the shaded part was "
        "0.93 of control (2-row); mung bean did better on the shaded side of the interspace",
    ),
    r(
        "poonia2024",
        crop="moth bean",
        season="kharif",
        years="2021",
        irrigated_or_rainfed="rainfed",
        **CAZRI,
        light_fraction=0.911,
        treatment_yield=670,
        control_yield=733,
        yield_unit="kg/ha",
        relative_yield=0.914,
        caveats="control derived (670 / 0.914); " + KHARIF_L + "; not a research-list crop",
    ),
    r(
        "poonia2024",
        crop="guar",
        variety="cluster bean",
        season="kharif",
        years="2021",
        irrigated_or_rainfed="rainfed",
        **CAZRI,
        light_fraction=0.911,
        treatment_yield=2008,
        control_yield=2277,
        yield_unit="kg/ha",
        relative_yield=0.882,
        caveats="control derived (2008 / 0.882); " + KHARIF_L + "; leeward half of the interspace yielded less",
    ),
    r(
        "poonia2024",
        crop="gram",
        variety="chickpea",
        season="rabi",
        years="2021-22",
        irrigated_or_rainfed="irrigated",
        **CAZRI,
        light_fraction=0.772,
        treatment_yield=2490,
        control_yield=2670,
        yield_unit="kg/ha",
        caveats=RABI_L + "; paper's spot midday PAR in the shaded part: 0.53 (2-row), 0.41 (3-row)",
    ),
    r(
        "poonia2024",
        crop="cumin",
        season="rabi",
        years="2021-22",
        irrigated_or_rainfed="irrigated",
        **CAZRI,
        light_fraction=0.772,
        treatment_yield=1000,
        control_yield=1120,
        yield_unit="kg/ha",
        caveats=RABI_L + "; paper's spot midday PAR in the shaded part: 0.58 (2-row), 0.56 (3-row)",
    ),
    r(
        "poonia2024",
        crop="isabgol",
        season="rabi",
        years="2021-22",
        irrigated_or_rainfed="irrigated",
        **CAZRI,
        light_fraction=0.772,
        treatment_yield=700,
        control_yield=760,
        yield_unit="kg/ha",
        caveats=RABI_L + "; paper's spot midday PAR in the shaded part: 0.46 (2-row), 0.68 (3-row); "
        "not a research-list crop",
    ),
    # Kyungpook, Korea (30% panel shading rate)
    r(
        "jo2022",
        crop="rice",
        variety="Wonkwang",
        season="kharif (summer)",
        years="2018",
        **KOREA,
        irrigated_or_rainfed="irrigated",
        control_yield=7.5,
        treatment_yield=6.1,
        yield_unit="t/ha",
        quality_notes="fewer spikelets and ripened grains per hill; 1000-grain weight unchanged",
    ),
    r(
        "jo2022",
        crop="rice",
        variety="Wonkwang",
        season="kharif (summer)",
        years="2019",
        **KOREA,
        irrigated_or_rainfed="irrigated",
        control_yield=7.9,
        treatment_yield=7.2,
        yield_unit="t/ha",
    ),
    r(
        "jo2022",
        crop="onion",
        variety="Honmaru",
        season="rabi (winter)",
        years="2018-19",
        **KOREA,
        relative_yield=0.806,
        yield_unit="bulb t/ha",
        caveats="yield index as printed; plot yields in Table 3",
    ),
    r(
        "jo2022",
        crop="onion",
        variety="Honmaru",
        season="rabi (winter)",
        years="2019-20",
        **KOREA,
        relative_yield=0.906,
        yield_unit="bulb t/ha",
        caveats="difference not significant",
    ),
    r(
        "jo2022",
        crop="soybean",
        variety="Hoshim",
        season="kharif (summer)",
        years="2020",
        **KOREA,
        control_yield=1.6,
        treatment_yield=0.5,
        yield_unit="t/ha",
        caveats="835 mm rain in Jul-Aug 2020 (very cloudy); 2019 difference not significant but values not printed "
        "in the text; treat as an outlier year",
    ),
    r(
        "jo2022",
        crop="maize",
        variety="Kwangpyeongok (forage)",
        season="kharif (summer)",
        years="2019",
        **KOREA,
        control_yield=55.1,
        treatment_yield=55.2,
        yield_unit="forage fresh t/ha",
        caveats="whole-plant forage, not grain",
    ),
    r(
        "jo2022",
        crop="maize",
        variety="Kwangpyeongok (forage)",
        season="kharif (summer)",
        years="2020",
        **KOREA,
        control_yield=41.8,
        treatment_yield=31.0,
        yield_unit="forage fresh t/ha",
        caveats="whole-plant forage, not grain; very wet year; difference not significant",
    ),
    # Japan: authors' threshold statement, not a treatment mean
    r(
        "gonocruz2021",
        crop="rice",
        season="kharif (summer)",
        years="2014-2019",
        irrigated_or_rainfed="irrigated",
        shading_method="APV",
        structure_type="fixed horizontal dummy panels 3 m high",
        clearance_m=3,
        module_type="wooden boards",
        shade_level_pct=33,
        light_fraction=0.67,
        light_measure="PPFD",
        light_method="measured shading rate (PPFD below vs above panels); 27-39% range",
        light_basis="measured_season",
        relative_yield=0.80,
        caveats="summary: authors conclude 27-39% shading keeps >= 80% of yield; derived from the regression in "
        "their Fig. 6, not a treatment mean",
        used_for="context_only",
    ),
    # Heggelbach, Germany
    r(
        "weselek2021",
        crop="wheat",
        variety="winter wheat",
        season="rabi (winter)",
        years="2017",
        **WESELEK,
        relative_yield=0.813,
        irrigated_or_rainfed="rainfed",
        caveats="temperate climate; organic farming",
    ),
    r(
        "weselek2021",
        crop="wheat",
        variety="winter wheat",
        season="rabi (winter)",
        years="2018",
        **WESELEK,
        relative_yield=1.027,
        irrigated_or_rainfed="rainfed",
        caveats="hot, dry summer: shade helped",
    ),
    r(
        "weselek2021",
        crop="potato",
        season="summer",
        years="2017",
        **WESELEK,
        relative_yield=0.818,
        irrigated_or_rainfed="rainfed",
        quality_notes="smaller share of tubers > 50 mm under AV",
    ),
    r(
        "weselek2021",
        crop="potato",
        season="summer",
        years="2018",
        **WESELEK,
        relative_yield=1.11,
        irrigated_or_rainfed="rainfed",
        caveats="hot, dry summer: shade helped",
    ),
    # Raichur shade nets
    *[
        r(
            "manoj2021",
            crop=c,
            variety=v,
            **MANOJ,
            shade_level_pct=s,
            light_fraction=1 - s / 100,
            light_method="nominal white net rating",
            control_yield=c0,
            treatment_yield=t,
            caveats="75% net yielded no less than 50% net, so the net ratings do not track the real light cut; "
            "excluded from fitting until measured light is found"
            + ("; not a research-list crop" if c == "cowpea" else ""),
        )
        for c, v, c0, pairs in (
            ("tur", "KBC-2 (pigeon pea)", 1823, ((50, 1447), (75, 1518))),
            ("urad", "black gram", 629, ((50, 433), (75, 435))),
            ("cowpea", "", 1054, ((50, 734), (75, 667))),
        )
        for s, t in pairs
    ],
    # IARI Delhi wheat, two seasons
    *[
        r(
            "mukherjee2020",
            crop="wheat",
            years=y,
            **MUKH,
            shade_level_pct=s,
            light_fraction=lf,
            control_yield=c0,
            treatment_yield=t,
            caveats=f"net rated {s}% shade",
        )
        for y, c0, pairs in (
            ("2014-15", 474.22, ((20, 0.784, 368.33), (35, 0.645, 250.56), (50, 0.469, 152.11), (75, 0.255, 93.33))),
            ("2015-16", 425.11, ((20, 0.744, 280.22), (35, 0.604, 181.11), (50, 0.427, 113.89), (75, 0.239, 51.33))),
        )
        for s, lf, t in pairs
    ],
    # Nanjing cotton: nets from flowering (50% bloom on FP1 of the 6th branch) to boll opening, 46-48 days
    *[
        r(
            "chen2017",
            crop="cotton",
            season="kharif (summer)",
            years=y,
            irrigated_or_rainfed="rainfed",
            shading_method="shade net",
            structure_type="white polyethylene nets > 2 m high, flowering to boll opening only",
            shade_level_pct=sh,
            light_fraction=1 - sh / 100,
            light_measure="solar radiation",
            light_method="share of solar radiation the nets blocked above the canopy on clear days",
            light_basis="measured_window",
            control_yield=c0,
            treatment_yield=t,
            yield_unit="kg/ha lint",
            quality_notes="fewer and lighter bolls; lower fibre strength and micronaire",
            caveats="shade only in the reproductive window (46-48 of about 150 days), the most sensitive phase; "
            "season-long shade at this level would likely cost more",
        )
        for y, c0, pairs in (("2010", 1703, ((21, 1374), (38, 1145))), ("2011", 1930, ((21, 1611), (38, 1346))))
        for sh, t in pairs
    ],
    # Jhansi mustard: net houses, yield per plant read from Fig. 1b (about +/- 2 g)
    *[
        r(
            "alam2018",
            crop="mustard",
            season="rabi",
            years="two seasons (mean)",
            irrigated_or_rainfed="irrigated",
            shading_method="shade net",
            structure_type="net houses 25 x 8 x 3 m rated 67, 50 and 25% light",
            light_fraction=lf,
            light_measure="PPFD",
            light_method="measured PPFD under each net vs open (09:30-10:00, Table 1)",
            light_basis="measured_spot",
            control_yield=69,
            treatment_yield=t,
            yield_unit="g/plant grain (read from figure)",
            n=30,
            caveats="per-plant yield read from a bar chart; net houses, not open field; "
            "authors put the critical limit at about 67% light",
        )
        for lf, t in ((0.641, 55), (0.467, 11), (0.245, 7))
    ],
    # Anand wheat APV (India): two light zones as tabulated in the 2026 review
    r(
        "prakash2025",
        crop="wheat",
        season="rabi",
        years="2017-2019",
        irrigated_or_rainfed="irrigated",
        shading_method="APV",
        structure_type="poly-Si APV",
        light_fraction=0.517,
        light_measure="PAR",
        light_method="PAR reduction 28-68.6% (midpoint used)",
        light_basis="measured_range",
        relative_yield=0.738,
        caveats="lighter zone; " + REVIEW,
    ),
    r(
        "prakash2025",
        crop="wheat",
        season="rabi",
        years="2017-2019",
        irrigated_or_rainfed="irrigated",
        shading_method="APV",
        structure_type="poly-Si APV",
        light_fraction=0.187,
        light_measure="PAR",
        light_method="PAR reduction 72.8-89.8% (midpoint used)",
        light_basis="measured_range",
        relative_yield=0.372,
        caveats="darker zone; " + REVIEW,
    ),
    # France maize APV
    *[
        r(
            "ramosfuentes2023",
            crop="maize",
            season="kharif (summer)",
            years="2019-2021",
            irrigated_or_rainfed="irrigated",
            shading_method="APV",
            structure_type="fixed and dynamic (tracking) APV",
            shade_level_pct=sh,
            light_fraction=1 - sh / 100,
            light_measure="shading",
            light_method=f"shading rate {txt}",
            light_basis="measured_range",
            relative_yield=ry,
            caveats=REVIEW,
        )
        for sh, txt, ry in ((35, "35%", 0.84), (32.5, "30-35%", 0.91), (55, "54-56%", 0.70))
    ],
    # Japanese rice APV
    r(
        "nasukawa2025",
        crop="rice",
        season="kharif (summer)",
        years="2021-2023",
        irrigated_or_rainfed="irrigated",
        shading_method="APV",
        structure_type="c-Si APV",
        shade_level_pct=32,
        light_fraction=0.68,
        light_measure="shading",
        light_method="shading rate 32%",
        light_basis="measured_range",
        relative_yield=0.866,
        quality_notes="protein content +6.4%",
        caveats=REVIEW,
    ),
    r(
        "thum2025",
        crop="rice",
        season="kharif (summer)",
        years="2018-2023",
        irrigated_or_rainfed="irrigated",
        shading_method="APV",
        structure_type="c-Si APV, modules over 27% of the field",
        light_fraction=0.745,
        light_measure="light",
        light_method="light reduction 21-30% (midpoint used)",
        light_basis="measured_range",
        control_yield=8.5,
        treatment_yield=6.5,
        yield_unit="t/ha",
        quality_notes="more chalky grain, lower head rice yield",
        caveats="six-year means as reported in pv magazine (2025-04-01) and the 2026 review; loss not significant "
        "in two of six years, larger in rainy years; primary paper not read (paywalled)",
    ),
    # Nigeria moong APV
    *[
        r(
            "ukwu2025",
            crop="moong",
            season="kharif",
            years="2022-2023",
            irrigated_or_rainfed="rainfed",
            shading_method="APV",
            structure_type="bifacial APV",
            light_fraction=lf,
            light_measure="PAR",
            light_method=f"PAR reduction {round(100 * (1 - lf))}%",
            light_basis="measured_range",
            relative_yield=ry,
            caveats=REVIEW + "; mean across genotypes",
        )
        for lf, ry in ((0.88, 1.23), (0.85, 0.81))
    ],
    # Brazil sugarcane APV
    r(
        "junior2025",
        crop="sugarcane",
        season="whole year",
        years="2022-2023",
        irrigated_or_rainfed="rainfed",
        shading_method="APV",
        structure_type="poly-Si APV with adjustable inter-unit distance",
        light_fraction=0.675,
        light_measure="PAR",
        light_method="65-70% PAR under APV (midpoint), as tabulated in the 2026 review",
        light_basis="measured_range",
        control_yield=59.10,
        treatment_yield=82.02,
        yield_unit="Mg/ha stalk",
        caveats="APV beat open field by 38.8% (higher leaf area index); one site, one season, cause not "
        "isolated (microclimate or water), so not used to fit a loss curve; yields from the paper's abstract",
        used_for="context_only",
    ),
]

# Laub (2022) crops kept, mapped to the research list (proxies noted)
LAUB_MAP = {
    "Soybean": ("soybean", ""),
    "Maize": ("maize", ""),
    "Wheat": ("wheat", ""),
    "Durum wheat": ("wheat", "durum wheat (proxy)"),
    "Barley": ("barley", "proxy for C3 cereals"),
    "Potato": ("potato", ""),
    "Peanut": ("groundnut", ""),
    "Chickpea": ("gram", "chickpea"),
    "Common bean": ("beans", "proxy for grain legumes"),
    "Black bean": ("beans", "proxy for grain legumes"),
    "Lupin": ("lupin", "proxy for grain legumes"),
}


def laub_rows(xlsx: Path) -> list[dict]:
    ws = openpyxl.load_workbook(xlsx, data_only=True).active
    out = []
    for v in ws.iter_rows(min_row=2, values_only=True):
        crop, _, rsr, yld, exp, zone, lat, lon, ghi, _, shade, ref, doi = v[:13]
        if crop not in LAUB_MAP or rsr is None or yld is None:
            continue
        name, note = LAUB_MAP[crop]
        out.append(
            r(
                "laub2022",
                crop=name,
                variety=note,
                country="",
                latitude=lat or "",
                longitude=lon or "",
                shading_method={
                    "Artificial shading": "shade net / cloth",
                    "Intercropping": "agroforestry / intercrop",
                }.get(exp, exp or ""),
                structure_type=f"{shade or ''}".replace("_", " "),
                shade_level_pct=rsr,
                light_fraction=round(1 - rsr / 100, 3),
                light_measure="solar radiation",
                light_method="reduction in solar radiation as compiled by Laub et al.",
                light_basis="compiled",
                relative_yield=round(yld / 100, 3),
                yield_unit="% of control",
                caveats=f"from Laub 2022 data set; original study: {ref} ({doi}); Laub climatic zone: {zone}; "
                f"GHI {ghi} kWh/m2/yr",
            )
        )
    return out


def main(research: Path) -> None:
    base = research / "09_crop_shade_response"
    rows = ROWS + laub_rows(base / "papers" / "raw" / "laub_2022_esm2.xlsx")
    for row in rows:
        row["used_for"] = row["used_for"] or "unassigned"
    out = base / "extraction" / "shade_response_extraction.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    bib = base / "papers" / "bibliography.csv"
    with bib.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["study_id", "citation", "doi_url", "peer_reviewed", "country", "study_type", "licence"])
        for sid, s in STUDIES.items():
            w.writerow(
                [sid, s["citation"], s["doi_url"], s["peer_reviewed"], s["country"], s["study_type"], s["licence"]]
            )
    print(len(rows), "rows ->", out)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
