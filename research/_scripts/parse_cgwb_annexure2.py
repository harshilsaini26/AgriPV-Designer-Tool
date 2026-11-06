"""Extract Annexure II (district-wise ground water resources, 2024) from the CGWB national compilation PDF.

Usage: uv run --no-project --with pymupdf python -I parse_cgwb_annexure2.py <pdf> <out.csv> [first_page last_page]

Default pages 169-206 (1-based) of "National Compilation on Dynamic Ground Water Resources of India, 2024".
The PDF's plain text layer moves the decimal point to the end of each number ("3049859\n."), so numeric
cells are rebuilt from individual characters sorted by x position (rawdict), which restores "30498.59".
Check a few rows against the printed PDF after any re-run.
"""

import csv
import re
import sys

import pymupdf

COLS = [
    "recharge_monsoon_rainfall_ham",
    "recharge_monsoon_other_ham",
    "recharge_nonmonsoon_rainfall_ham",
    "recharge_nonmonsoon_other_ham",
    "total_annual_recharge_ham",
    "total_natural_discharges_ham",
    "annual_extractable_resource_ham",
    "extraction_irrigation_ham",
    "extraction_industrial_ham",
    "extraction_domestic_ham",
    "extraction_total_ham",
    "allocation_domestic_2025_ham",
    "net_availability_future_ham",
    "stage_of_extraction_pct",
]


def num(page, bbox):
    """Rebuild a number from the characters inside one cell, ordered left to right."""
    if bbox is None:
        return ""
    raw = page.get_text("rawdict", clip=pymupdf.Rect(bbox))
    chars = [
        (ch["origin"][0], ch["c"])
        for b in raw["blocks"]
        for line in b.get("lines", [])
        for span in line["spans"]
        for ch in span["chars"]
    ]
    s = "".join(c for _, c in sorted(chars) if c in "0123456789.-")
    if s in ("", "-", "."):
        return ""
    return str(float(s))


def main(pdf, out, first=169, last=206):
    doc = pymupdf.open(pdf)
    rows_out = []
    state = ""
    for pn in range(first, last + 1):
        page = doc[pn - 1]
        for table in page.find_tables().tables:
            for r, row in zip(table.extract(), table.rows):
                c0 = (r[0] or "").strip()
                rest = [x for x in r[1:] if x not in (None, "")]
                if c0 and not rest and not c0.startswith("DYNAMIC"):
                    state = re.sub(r"\s+", " ", c0).strip(" ,")
                    continue
                if re.fullmatch(r"\d+", c0) and len(r) >= 16 and r[1] and not re.fullmatch(r"\d+", r[1].strip()):
                    values = [num(page, bbox) for bbox in row.cells[2:16]]
                    rows_out.append([state, re.sub(r"\s+", " ", r[1]).strip(), *values, pn])
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["state", "district", *COLS, "pdf_page"])
        w.writerows(rows_out)
    print(len(rows_out), "district rows ->", out)


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0], args[1], *(int(a) for a in args[2:4]))
