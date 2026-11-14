"""Draft (L_t, k) shade-response parameters and evidence grades for the AgriPV Lab research crops (spec §12, §13).

Usage: uv run --no-project --with python-docx --with numpy python -I fit_shade_parameters.py <research_dir>

Model (spec §12): Y_rel = 1 if L >= L_t, else max(0, 1 - k (L_t - L)), with L the light fraction at the crop.

1. Group curves: Laub et al. (2022) Table S2 gives the meta-analysis mean yield and 95% CI per crop type at 5-90%
   reduction in solar radiation (local copy of ESM 1). (L_t, k) is fitted to the mean (central), the lower CI
   (low = pessimistic) and the upper CI (high = optimistic) over light fractions 0.4-0.95, the range agrivoltaic
   systems produce. Yields above 100% are capped at 1, as the model cannot represent a shade benefit.
2. Crop curves: crops with >= 8 usable points from >= 3 studies spanning >= 0.3 of light fraction are fitted to
   their own points (central); low / high keep the group spread around it. Otherwise the crop takes its group curve.
   A crop with no group but >= 3 points spanning >= 0.10 of light (cotton, mustard, sesame) is fitted to
   its own points with an assumed spread (threshold +/-0.05, slope +/-25%).
3. Grade (spec §13.3): A >= 2 Indian field studies; B 1 Indian study or >= 2 international studies; C 1
   international study or extension from a closely related crop group; D no data and no close group.
Writes 09_crop_shade_response/parameters/crop_parameters_draft.csv and group_curves_laub2022.csv.
"""

import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

import docx
import numpy as np

# research crop -> (Laub group used as the prior, how close the group is, seasons, extra crops whose rows count)
CROPS = {
    "rice": ("C3 cereals", "own group", "kharif, rabi, summer", []),
    "wheat": ("C3 cereals", "own group", "rabi", []),
    "soybean": ("Grain legumes", "own group", "kharif", []),
    "cotton": (None, "no close group", "kharif", []),
    "maize": ("Maize", "own group", "kharif, rabi, summer", []),
    "gram": ("Grain legumes", "own group", "rabi", []),
    "mustard": (None, "no close group (C3 oilseed; brassica)", "rabi", []),
    "bajra": ("Maize", "related (C4 cereal)", "kharif, summer", []),
    "sugarcane": ("Maize", "related (C4 grass of the same tribe as maize and sorghum; 10-18 months)", "whole year", []),
    "moong": ("Grain legumes", "own group", "kharif, summer", []),
    "groundnut": ("Grain legumes", "own group", "kharif, rabi, summer", []),
    "tur": ("Grain legumes", "own group", "kharif", []),
    "jowar": ("Maize", "related (C4 cereal)", "kharif, rabi", []),
    "urad": ("Grain legumes", "own group", "kharif, rabi, summer", []),
    "guar": ("Grain legumes", "own group", "kharif", []),
    "potato": ("Tubers/root crops", "own group", "rabi", []),
    "onion": ("Tubers/root crops", "related (bulb vegetable)", "rabi, kharif", []),
    "lentil": ("Grain legumes", "own group", "rabi", []),
    "sesame": (None, "no close group", "kharif, summer", []),
    "cumin": (None, "no close group (seed spice)", "rabi", []),
}
GRID = [(lt, k) for lt in np.arange(0.40, 1.0001, 0.01) for k in np.arange(0.0, 6.0001, 0.02)]


def model(lt: float, k: float, light: np.ndarray) -> np.ndarray:
    return np.where(light >= lt, 1.0, np.maximum(0.0, 1 - k * (lt - light)))


def fit(light, y) -> tuple[float, float, float]:
    light, y = np.asarray(light, float), np.minimum(np.asarray(y, float), 1.0)
    best = min(GRID, key=lambda p: float(np.sum((model(p[0], p[1], light) - y) ** 2)))
    rmse = float(np.sqrt(np.mean((model(*best, light) - y) ** 2)))
    return round(float(best[0]), 2), round(float(best[1]), 2), round(rmse, 3)


def laub_table_s2(path: Path) -> dict:
    """{group: [(light, mean, lo, hi), ...]} from Table S2 of the Laub ESM 1 docx."""
    out = defaultdict(list)
    for t in docx.Document(path).tables:
        head = [c.text.strip() for c in t.rows[0].cells]
        if head[:3] != ["Crop type", "RSR", "Prediction"]:
            continue
        for row in t.rows[1:]:
            c = [x.text.strip() for x in row.cells]
            for off in (1, 5):
                m = re.match(r"\(([\d.]+)\s*-\s*([\d.]+)\)", c[off + 2])
                if m:
                    out[c[0]].append(
                        (1 - float(c[off]) / 100, float(c[off + 1]) / 100, float(m[1]) / 100, float(m[2]) / 100)
                    )
    return out


def in_india(lat, lon) -> bool:
    try:
        return 6 <= float(lat) <= 37 and 68 <= float(lon) <= 98
    except ValueError:
        return False


def main(research: Path) -> None:
    base = research / "09_crop_shade_response"
    s2 = laub_table_s2(base / "papers" / "raw" / "laub_2022_esm1.docx")
    groups = {}
    with (base / "parameters" / "group_curves_laub2022.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(
            [
                "crop_group",
                "lt_low",
                "k_low",
                "lt_central",
                "k_central",
                "lt_high",
                "k_high",
                "rmse_central",
                "n_points",
            ]
        )
        for g, pts in sorted(s2.items()):
            pts = [p for p in pts if 0.4 <= p[0] <= 0.95]
            light = [p[0] for p in pts]
            fits = {name: fit(light, [p[i] for p in pts]) for name, i in (("low", 2), ("central", 1), ("high", 3))}
            groups[g] = fits
            w.writerow([g, *fits["low"][:2], *fits["central"][:2], *fits["high"][:2], fits["central"][2], len(pts)])

    rows = list(csv.DictReader((base / "extraction" / "shade_response_extraction.csv").open(encoding="utf-8")))
    data = defaultdict(list)
    for r in rows:
        if r["used_for"] == "context_only" or "outlier" in r["caveats"] or "forage" in r["yield_unit"]:
            continue
        if r["light_basis"].startswith("nominal_net"):  # net ratings that do not track the measured light
            continue
        if r["light_fraction"] == "" or r["relative_yield"] == "":
            continue
        indian = r["country"] == "India" or (r["study_id"] == "laub2022" and in_india(r["latitude"], r["longitude"]))
        orig = r["caveats"].split("original study: ")[1].split(" (")[0] if r["study_id"] == "laub2022" else ""
        data[r["crop"]].append((float(r["light_fraction"]), float(r["relative_yield"]), r["study_id"], orig, indian))

    out = base / "parameters" / "crop_parameters_draft.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(
            [
                "crop",
                "seasons",
                "tolerance_group",
                "group_fit",
                "lt_low",
                "lt_central",
                "lt_high",
                "k_low",
                "k_central",
                "k_high",
                "parameter_source",
                "grade",
                "n_points",
                "n_studies",
                "n_indian_studies",
                "light_range",
                "rmse_vs_points",
                "study_ids",
                "notes",
            ]
        )
        for crop, (group, closeness, seasons, _) in CROPS.items():
            pts = data.get(crop, [])
            studies = {(p[2], p[3]) for p in pts}
            indian = {s for s, p in zip(((p[2], p[3]) for p in pts), pts) if p[4]}
            light = [p[0] for p in pts]
            span = (max(light) - min(light)) if light else 0
            notes = []
            if group:
                g = groups[group]
                low, cen, high = g["low"], g["central"], g["high"]
                source = f"Laub 2022 group curve ({group})"
            else:
                low = cen = high = ("", "", "")
                source = "none yet"
            if len(pts) >= 8 and len(studies) >= 3 and span >= 0.3:
                own = fit(light, [p[1] for p in pts])
                if group:  # keep the group's spread around the crop's own central fit
                    dl, dk = own[0] - cen[0], own[1] - cen[1]
                    low = (round(min(1.0, max(0.4, low[0] + dl)), 2), round(max(0, low[1] + dk), 2))
                    high = (round(min(1.0, max(0.4, high[0] + dl)), 2), round(max(0, high[1] + dk), 2))
                cen = own
                source = f"fitted to {len(pts)} points" + (f"; spread from {group} group" if group else "")
            elif not group and len(pts) >= 3 and span >= 0.10:
                # no group to lean on: fit the crop's own points and assume a +/-25% slope and +/-0.05 threshold spread
                cen = fit(light, [p[1] for p in pts])
                low = (round(min(1.0, cen[0] + 0.05), 2), round(cen[1] * 1.25, 2))
                high = (round(cen[0] - 0.05, 2), round(cen[1] * 0.75, 2))
                source = f"fitted to {len(pts)} points from {len(studies)} {'study' if len(studies) == 1 else 'studies'}; spread assumed"
                notes.append("few studies: spread is assumed (threshold +/-0.05, slope +/-25%), not measured")
            rmse = ""
            if pts and cen[0] != "":
                rmse = round(
                    float(
                        np.sqrt(
                            np.mean((model(cen[0], cen[1], np.array(light)) - np.minimum([p[1] for p in pts], 1)) ** 2)
                        )
                    ),
                    3,
                )
            n_ind, n_int = len(indian), len(studies) - len(indian)
            if n_ind >= 2:
                grade = "A"
            elif n_ind == 1 or n_int >= 2:
                grade = "B"
            elif n_int == 1 or (group and closeness != "no close group"):
                grade = "C"
            else:
                grade = "D"
            if cen[0] == "":
                grade = "D"
                if pts:
                    notes.append(f"{len(pts)} point(s) on file but no group curve to anchor a fit")
            if rmse != "" and rmse > 0.15:
                notes.append(
                    f"curve misses the observed points (RMSE {rmse}); Indian trials report light differently "
                    "(spot or nominal values), so check the light metric before refitting"
                    if n_ind
                    else f"curve misses the observed points (RMSE {rmse})"
                )
            if group and closeness.startswith("related"):
                notes.append(f"group curve borrowed from a related group: {closeness}")
            if not group and cen[0] == "":
                notes.append(f"no parameters yet: {closeness}")
            w.writerow(
                [
                    crop,
                    seasons,
                    group or "",
                    closeness,
                    low[0],
                    cen[0],
                    high[0],
                    low[1],
                    cen[1],
                    high[1],
                    source,
                    grade,
                    len(pts),
                    len(studies),
                    n_ind,
                    f"{min(light):.2f}-{max(light):.2f}" if light else "",
                    rmse,
                    "; ".join(sorted({s if not o else f"{s}:{o}" for s, o in studies})),
                    "; ".join(notes),
                ]
            )
    print("groups:", {g: f["central"] for g, f in groups.items()})
    print("->", out)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
