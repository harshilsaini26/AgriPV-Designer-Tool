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
    "light_measure": "PAR",
    "light_method": "spot midday PAR in the shaded part of the interspace vs control (9:00-15:00); the sunlit part "
    "of the interspace gets more, so the interspace daily mean is higher than this value",
}
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
}
WESELEK = {
    "shading_method": "APV",
    "structure_type": "elevated overhead APV (Heggelbach research plant)",
    "module_type": "bifacial glass-glass",
    "shade_level_pct": 30,
    "light_fraction": 0.70,
    "light_measure": "PAR",
    "light_method": "measured: mean daily PAR about 30% lower under AV than reference, both years",
}
MANOJ = {
    "shading_method": "shade net",
    "structure_type": "white shade nets from 25 DAS to harvest",
    "light_measure": "nominal",
    "years": "two seasons (mean)",
    "season": "kharif",
    "irrigated_or_rainfed": "rainfed",
    "yield_unit": "kg/ha grain",
}
MUKH = {
    "shading_method": "shade net",
    "structure_type": "shade nets rated 20/35/50/75% over the whole season",
    "light_measure": "nominal",
    "light_method": "nominal net rating; measured global radiation at 61 DAS was 0.76/0.65/0.41/0.22 of control "
    "in 2014-15",
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
        light_fraction=0.93,
        treatment_yield=1155,
        control_yield=1211,
        yield_unit="kg/ha",
        relative_yield=0.954,
        caveats="control derived (1155 / 0.954); light 0.93 is the 2-row array value (3-row value printed as 392 vs "
        "1233 µmol, inconsistent with the stated 7%); mung bean did better on the shaded side of the interspace",
    ),
    r(
        "poonia2024",
        crop="moth bean",
        season="kharif",
        years="2021",
        irrigated_or_rainfed="rainfed",
        **CAZRI,
        treatment_yield=670,
        control_yield=733,
        yield_unit="kg/ha",
        relative_yield=0.914,
        caveats="control derived (670 / 0.914); no PAR value printed for moth bean; not a research-list crop",
    ),
    r(
        "poonia2024",
        crop="guar",
        variety="cluster bean",
        season="kharif",
        years="2021",
        irrigated_or_rainfed="rainfed",
        **CAZRI,
        treatment_yield=2008,
        control_yield=2277,
        yield_unit="kg/ha",
        relative_yield=0.882,
        caveats="control derived (2008 / 0.882); no PAR value printed for cluster bean; "
        "leeward half of the interspace yielded less",
    ),
    r(
        "poonia2024",
        crop="gram",
        variety="chickpea",
        season="rabi",
        years="2021-22",
        irrigated_or_rainfed="irrigated",
        **CAZRI,
        light_fraction=0.47,
        treatment_yield=2490,
        control_yield=2670,
        yield_unit="kg/ha",
        caveats="light = mean of 2-row (0.53) and 3-row (0.41) spot PAR",
    ),
    r(
        "poonia2024",
        crop="cumin",
        season="rabi",
        years="2021-22",
        irrigated_or_rainfed="irrigated",
        **CAZRI,
        light_fraction=0.57,
        treatment_yield=1000,
        control_yield=1120,
        yield_unit="kg/ha",
        caveats="light = mean of 2-row (0.58) and 3-row (0.56) spot PAR",
    ),
    r(
        "poonia2024",
        crop="isabgol",
        season="rabi",
        years="2021-22",
        irrigated_or_rainfed="irrigated",
        **CAZRI,
        light_fraction=0.57,
        treatment_yield=700,
        control_yield=760,
        yield_unit="kg/ha",
        caveats="light = mean of 2-row (0.46) and 3-row (0.68) spot PAR; not a research-list crop",
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
            caveats="75% net yielded no less than 50% net, so net ratings may overstate the real light cut"
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
            light_fraction=1 - s / 100,
            control_yield=c0,
            treatment_yield=t,
        )
        for y, c0, pairs in (
            ("2014-15", 474.22, ((20, 368.33), (35, 250.56), (50, 152.11), (75, 93.33))),
            ("2015-16", 425.11, ((20, 280.22), (35, 181.11), (50, 113.89), (75, 51.33))),
        )
        for s, t in pairs
    ],
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
