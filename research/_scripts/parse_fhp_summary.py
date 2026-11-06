"""Extract Table 2 (major crop × state average farm harvest prices, 4 years) from the DES FHP report.

Usage: uv run --no-project --with pymupdf python -I parse_fhp_summary.py <pdf> <out.csv> [first last]
Default PDF pages 10-18 of "Farm Harvest Prices of Principal Crops in India 2022-23".
Each page: header "States / 2019-20 … 2022-23 / Trendline", then state name + 4 values ("NR" = not reported),
then the caption "<Crop> : State-Wise Average Farm Harvest Prices … (in Rs/ Quintal)".
"""

import csv
import re
import sys

import pymupdf

YEAR = re.compile(r"^\d{4}-\d{2}$")
VALUE = re.compile(r"^(\d+(\.\d+)?|NR|-)$")


def main(pdf, out, first=10, last=18):
    doc = pymupdf.open(pdf)
    rows = []
    for pn in range(first, last + 1):
        text = doc[pn - 1].get_text()
        m = re.search(r"([^\n]+?)\s*:\s*State-Wise Average Farm Harvest Prices", text)
        if not m:
            continue
        crop = m.group(1).strip()
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        header = next(i for i, ln in enumerate(lines) if ln.startswith("States"))
        years = re.findall(r"\d{4}-\d{2}", lines[header] + " " + lines[header + 1])
        i = header + 1
        while i < len(lines) and not lines[i].startswith("Trendline"):
            i += 1
        i += 1
        while i + len(years) < len(lines):
            name, vals = lines[i], lines[i + 1 : i + 1 + len(years)]
            if not all(VALUE.match(v) for v in vals) or VALUE.match(name):
                break
            for y, v in zip(years, vals):
                rows.append([crop, name, y, "" if v in ("NR", "-") else v, pn])
            i += 1 + len(years)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["crop", "state", "year", "fhp_inr_per_qtl", "pdf_page"])
        w.writerows(rows)
    print(len(rows), "values;", sorted({r[0] for r in rows}))


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], *(int(x) for x in a[2:4]))
