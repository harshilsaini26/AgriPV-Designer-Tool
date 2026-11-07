"""National crop ranking by area (answers open question Q-04) from the local UPAg district APY files.

Usage: python -I upag_national_crop_ranking.py <research_dir>

Sums the "Crop-wise Data" area rows over districts per crop and season, for **2023-24 and 2024-25 only**: those two
years reconcile with the All-India final estimates (rice 478.2 and wheat 318.2 lakh ha in 2023-24), while
2019-20 to 2022-23 label eastern-state winter (Aman) rice as rabi and over-count wheat in MP / UP / Rajasthan by
about 12 %. Aggregates (Cereals, Total Pulses, ...) and the overlapping "Jute & Mesta" row are excluded.
UPAg has no horticulture, so potato, onion, tomato, mango, banana and coconut are appended without area values.
Ranks 1-15 are "firm"; 16-20 are "contested" with the horticulture crops, whose areas (roughly 15-25 lakh ha
each) would push some of them out. Writes 06_crops/area_production_yield/top20_national.csv.
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path

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
HORTICULTURE = ["Potato", "Onion", "Tomato", "Mango", "Banana", "Coconut"]


def main(research: Path) -> None:
    apy = research / "06_crops" / "area_production_yield"
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
    crops = defaultdict(float)
    for (c, _), v in area.items():
        crops[c] += v
    ranked = sorted(crops, key=lambda c: -crops[c])
    out = apy / "top20_national.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "rank",
                "crop",
                "area_lakh_ha",
                "kharif_pct",
                "rabi_pct",
                "summer_pct",
                "yield_kg_ha",
                "top20_status",
                "note",
            ]
        )
        for i, c in enumerate(ranked, 1):
            tot = crops[c]
            pr = sum(prod[(c, s)] for s in SEASONS)
            unit = "yield blank: production in bales" if c in ("Cotton", "Jute", "Mesta", "Sannhemp") else ""
            y = round(1000 * pr / tot) if tot else ""
            if c in ("Cotton", "Jute", "Mesta", "Sannhemp"):
                y = ""  # production in bales; see the UPAg card for factors
            w.writerow(
                [
                    i,
                    c,
                    round(tot / 1e5, 2),
                    *[round(100 * area[(c, s)] / tot, 1) for s in SEASONS],
                    y,
                    "firm" if i <= 15 else "contested" if i <= 20 else "no",
                    unit,
                ]
            )
        for c in HORTICULTURE:
            w.writerow(
                [
                    "",
                    c,
                    "",
                    "",
                    "",
                    "",
                    "",
                    "contested",
                    "horticulture: not in UPAg; national area to confirm from DA&FW horticulture estimates",
                ]
            )
    print(len(ranked), "crops ->", out)
    for c in ranked[:22]:
        print(f"{c:22s} {crops[c] / 1e5:7.2f}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
