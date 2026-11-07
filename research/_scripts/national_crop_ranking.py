"""National crop ranking by area, field and horticulture crops together (answers open question Q-04).

Usage: uv run --no-project --with xlrd python -I national_crop_ranking.py <research_dir>

Field crops: the local UPAg district APY files, "Crop-wise Data" area rows summed over districts per crop and
season, for **2023-24 and 2024-25 only**. Those two years reconcile with the All-India final estimates (rice 478.2
and wheat 318.2 lakh ha in 2023-24); 2019-20 to 2022-23 label eastern-state winter (Aman) rice as rabi and
over-count wheat in MP / UP / Rajasthan by about 12 %. Aggregates and the overlapping "Jute & Mesta" row are
excluded.

Horticulture: the DA&FW "Area and Production of Horticulture crops for 2024-25 (Final Estimates)" workbook,
Summary sheet, which carries both the 2023-24 Final and 2024-25 Final columns ('000 ha, '000 t; coconut
by weight, not nut count). Group totals (Citrus Total, Total Fruits, ...) and "Other ..." rows are excluded; the citrus
species are kept separately.
Both sources give the mean of the same two years. Writes 06_crops/area_production_yield/top20_national.csv.
"""

import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

import xlrd

YEARS = ["2023-24", "2024-25"]
SEASONS = ["Kharif", "Rabi", "Summer"]
SKIP = {
    "Cereals",
    "Total Pulses",
    "Total Food Grains",
    "Nutri/Coarse Cereals",
    "Shree Anna /Nutri Cereals",
    "Jute & Mesta",
    "Other Pulses",
    "Small Millets",
}
BALES = {"Cotton", "Jute", "Mesta", "Sannhemp"}
# Summary-sheet section headers -> group label
HORT_GROUPS = {
    "Fruits": "fruit",
    "Vegetables": "vegetable",
    "Plantation Crops": "plantation",
    "Spices": "spice",
    "Aromatics and Medicinal": "aromatic / medicinal",
    "Flowers Cut": "flower",
}
PERENNIAL = {
    "Mango", "Coconut", "Cashewnut", "Arecanut", "Banana", "Apple", "Guava", "Walnut", "Grapes", "Pomegranate",
    "Jackfruit", "Litchi", "Sapota", "Black Pepper", "Cardamom", "Cocoa", "Aonla/Gooseberry", "Ber",
    "(i)   Lime/Lemon", "(ii) Mandarin", "(iii) Sweet Orange (Mosambi)", "(iv) Other Citrus",
}  # fmt: skip


def field_crops(apy: Path) -> list[dict]:
    area = defaultdict(float)
    prod = defaultdict(float)
    for y in YEARS:
        p = apy / "raw" / "upag_des_district" / f"upag_des_district_apy_{y}_long.csv"
        with p.open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r["Total Type"] != "Crop-wise Data" or r["Season"] not in SEASONS or r["Crop"] in SKIP:
                    continue
                try:
                    v = float(r["Value"])
                except ValueError:
                    continue
                if r["Metric"] == "Area":
                    area[(r["Crop"], r["Season"])] += v / len(YEARS)
                elif r["Metric"] == "Production":
                    prod[(r["Crop"], r["Season"])] += v / len(YEARS)
    out = []
    for c in sorted({c for c, _ in area}):
        tot = sum(area[(c, s)] for s in SEASONS)
        pr = sum(prod[(c, s)] for s in SEASONS)
        out.append(
            {
                "crop": c,
                "group": "field crop",
                "area_lakh_ha": tot / 1e5,
                "kharif_pct": round(100 * area[(c, "Kharif")] / tot, 1),
                "rabi_pct": round(100 * area[(c, "Rabi")] / tot, 1),
                "summer_pct": round(100 * area[(c, "Summer")] / tot, 1),
                "yield": "" if c in BALES else round(1000 * pr / tot),
                "yield_unit": "production in bales" if c in BALES else "kg/ha",
                "source": "UPAg (DES district APY, summed)",
            }
        )
    return out


def horticulture(apy: Path) -> list[dict]:
    book = xlrd.open_workbook(apy / "raw" / "dafw_horticulture" / "2024_25_Final_Estimates.xls")
    sh = book.sheet_by_name("Summary")
    group, out = None, []
    for r in range(sh.nrows):
        v = sh.row_values(r)
        name = str(v[1]).strip()
        if name in HORT_GROUPS:
            group = HORT_GROUPS[name]
            continue  # header row; "Aromatics and Medicinal" carries only a group total
        if group is None or not name or name.startswith(("Total", "Other", "Citrus")):
            continue
        try:
            a = [float(v[2]), float(v[6])]  # '000 ha: 2023-24 Final, 2024-25 Final
            p = [float(v[3]), float(v[7])]
        except ValueError:
            continue
        a_mean, p_mean = sum(a) / 2, sum(p) / 2
        out.append(
            {
                "crop": re.sub(r"^\([ivx]+\)\s*", "", " ".join(name.split())),
                "group": group + (" (perennial)" if name in PERENNIAL else ""),
                "area_lakh_ha": a_mean / 100,
                "kharif_pct": "",
                "rabi_pct": "",
                "summer_pct": "",
                "yield": round(1e3 * p_mean / a_mean) if a_mean else "",  # '000 t / '000 ha -> kg/ha
                "yield_unit": "kg/ha (nut weight)" if name == "Coconut" else "kg/ha",
                "source": "DA&FW horticulture final estimates",
            }
        )
    return out


def main(research: Path) -> None:
    apy = research / "06_crops" / "area_production_yield"
    rows = sorted(field_crops(apy) + horticulture(apy), key=lambda d: -d["area_lakh_ha"])
    path = apy / "top20_national.csv"
    cols = ["rank", "crop", "group", "area_lakh_ha", "kharif_pct", "rabi_pct", "summer_pct", "yield", "yield_unit"]
    # Research list (owner decision 2026-11-07): the 20 largest *annual* crops. Perennial tree crops (mango,
    # coconut, ...) are skipped because panels cannot be built over a mature orchard or plantation.
    research_list = [d["crop"] for d in rows if "perennial" not in d["group"]][:20]
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow([*cols, "top20_by_area", "research_list", "source"])
        for i, d in enumerate(rows[:40], 1):
            d["area_lakh_ha"] = round(d["area_lakh_ha"], 2)
            w.writerow([i, *[d[c] for c in cols[1:]], i <= 20, d["crop"] in research_list, d["source"]])
    print(len(rows), "crops; top 40 ->", path)
    print("research list:", ", ".join(research_list))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
