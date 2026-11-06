"""Convert a DES "Horizontal Crop Vertical Year" report (HTML saved as .xls) to a tidy long CSV.

Usage: python -I parse_des_horizontal_report.py <report.xls> <out.csv>

The report's <thead> has three rows (crop / season / metric). Body rows use rowspan for State and
District, so a row carries 3, 2 or 1 leading label cells before the data cells.
"""

import csv
import html
import re
import sys


def text(cell: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", cell))).strip()


def strip_number_prefix(label: str) -> str:
    return re.sub(r"^\d+\.\s*", "", label)


def main(src: str, out: str) -> None:
    s = open(src, encoding="utf-8", errors="replace").read()
    thead = re.sub(r"<!--.*?-->", "", s[: s.find("<tbody")], flags=re.S)
    head_rows = [re.findall(r"<th[^>]*>(.*?)</th>", tr, re.S) for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", thead, re.S)]
    crops = [text(c) for c in head_rows[0][3:]]
    seasons = [text(c) for c in head_rows[1]]
    metrics = [text(c) for c in head_rows[2]]
    columns = []  # (crop, season, metric, unit) per data cell
    for i, m in enumerate(metrics):
        crop, season = crops[i // 3], seasons[i // 3]
        name, unit = re.match(r"(\w+) \((.+)\)", m).groups()
        columns.append((crop, season, name, unit))

    body = s[s.find("<tbody") :]
    state = district = ""
    n = 0
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["state", "district", "crop_year", "crop", "season", "metric", "unit", "value"])
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.S):
            cells = [text(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            lead = len(cells) - len(columns)
            if lead == 3:
                state, district = strip_number_prefix(cells[0]), strip_number_prefix(cells[1])
            elif lead == 2:
                district = strip_number_prefix(cells[0])
            elif lead != 1:
                continue  # totals or malformed rows
            year = cells[lead - 1].replace(" ", "")
            for (crop, season, metric, unit), v in zip(columns, cells[lead:]):
                if v == "":
                    continue
                w.writerow([state, district, year, crop, season, metric, unit, v.replace(",", "")])
                n += 1
    print(f"{len(columns)} columns, {n} values -> {out}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
