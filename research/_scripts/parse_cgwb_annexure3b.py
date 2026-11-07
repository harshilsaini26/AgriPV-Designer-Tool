"""Extract Annexure III(B) (district-wise categorisation of assessment units) from a CGWB national compilation.

Usage: uv run --no-project --with pymupdf python -I parse_cgwb_annexure3b.py <pdf> <out.csv> <first_page> <last_page>

2025 edition: pages 216-262. Only the unit counts are read; some states print them with decimals ("1.00"),
and the PDF text layer moves the decimal point to the end, so each count cell is rebuilt from characters ordered by x
position
and rounded. Percentages are recomputed from the counts. Rows whose categories do not sum to the total are flagged.
"""

import csv
import re
import sys

import pymupdf

CATS = ["safe", "semi_critical", "critical", "over_exploited", "saline"]
COUNT_COLS = [3, 5, 7, 9, 11]  # "No." columns; percent columns sit in between


def as_int(page, bbox) -> int:
    if bbox is None:
        return 0
    raw = page.get_text("rawdict", clip=pymupdf.Rect(bbox))
    chars = [
        (ch["origin"][0], ch["c"])
        for b in raw["blocks"]
        for ln in b.get("lines", [])
        for sp in ln["spans"]
        for ch in sp["chars"]
    ]
    s = "".join(c for _, c in sorted(chars) if c in "0123456789.")
    return round(float(s)) if s.strip(".") else 0


def main(pdf: str, out: str, first: int, last: int) -> None:
    doc = pymupdf.open(pdf)
    rows, state = [], ""
    for pn in range(first, last + 1):
        page = doc[pn - 1]
        for table in page.find_tables().tables:
            for r, row in zip(table.extract(), table.rows):
                c0 = (r[0] or "").strip()
                rest = [x for x in r[1:] if x not in (None, "")]
                if c0 and not rest and not c0.startswith("DYNAMIC"):
                    state = re.sub(r"\s+", " ", c0).strip(" ,")
                    continue
                if not re.fullmatch(r"\d+", c0) or len(r) < 12 or not r[1]:
                    continue
                total = as_int(page, row.cells[2])
                counts = [as_int(page, row.cells[i]) for i in COUNT_COLS]
                rows.append([state, re.sub(r"\s+", " ", r[1]).strip(), total, *counts, sum(counts) == total, pn])
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "state",
                "district",
                "units_total",
                *[f"units_{c}" for c in CATS],
                "pct_units_critical_or_over_exploited",
                "counts_sum_ok",
                "pdf_page",
            ]
        )
        for st, dist, total, *rest in rows:
            counts, ok, pn = rest[:5], rest[5], rest[6]
            pct = round(100 * (counts[2] + counts[3]) / total, 1) if total else ""
            w.writerow([st, dist, total, *counts, pct, ok, pn])
    bad = sum(1 for r in rows if not r[8])
    print(len(rows), "district rows;", bad, "with counts not summing to total ->", out)


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], int(a[2]), int(a[3]))
