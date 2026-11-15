"""State-level crop economics and example crops for the app (model-slice spec §5).

Source: DES cost of cultivation, as published on the India Data Portal (ODC-By). Values are per hectare in
the source and per acre here.
"""

import statistics
from collections import Counter

from pipeline.appdata.states import canonical_state

HECTARE_IN_ACRES = 2.4711
OLDEST_YEAR = "2018-19"
SOURCE = "DES cost of cultivation (A2+FL), via India Data Portal"
CROP_NAME_MAP = {
    "Paddy": "rice",
    "Wheat": "wheat",
    "Soyabean": "soybean",
    "Cotton": "cotton",
    "Maize": "maize",
    "Gram": "gram",
    "Rapeseed & Mustard (Toria/Taramira)": "mustard",
    "Bajra": "bajra",
    "Sugarcane": "sugarcane",
    "Moong": "moong",
    "Groundnut": "groundnut",
    "Tur (Arhar)": "tur",
    "Jowar": "jowar",
    "Urad": "urad",
    "Potato": "potato",
    "Onion": "onion",
    "Masur": "lentil",
    "Lentil": "lentil",
    "Sesamum (Til)": "sesame",
}


def _number(value) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if x > 0 else None


def _latest_rows(rows: list[dict]) -> dict[tuple[str, str], dict]:
    """The latest usable row for each (state, crop id)."""
    latest: dict[tuple[str, str], dict] = {}
    for r in rows:
        crop_id = CROP_NAME_MAP.get(r.get("crop_name", ""))
        year = r.get("year", "")
        if crop_id is None or year < OLDEST_YEAR:
            continue
        if not all(_number(r.get(c)) for c in ("derived_yield", "main_product_value", "cul_cost_a2fl")):
            continue
        key = (canonical_state(r["state_name"]), crop_id)
        if key not in latest or year > latest[key]["year"]:
            latest[key] = r
    return latest


def _entry(r: dict) -> dict:
    yield_ha = float(r["derived_yield"])
    return {
        "yield_q_per_acre": round(yield_ha / HECTARE_IN_ACRES, 2),
        "price_per_q": round(float(r["main_product_value"]) / yield_ha),
        "cost_per_acre": round(float(r["cul_cost_a2fl"]) / HECTARE_IN_ACRES),
        "year": r["year"],
        "basis": "state",
    }


def build_crop_economics(rows: list[dict]) -> dict:
    by_state: dict[str, dict[str, dict]] = {}
    for (state, crop_id), r in sorted(_latest_rows(rows).items()):
        by_state.setdefault(state, {})[crop_id] = _entry(r)
    per_crop: dict[str, list[dict]] = {}
    for crops in by_state.values():
        for crop_id, e in crops.items():
            per_crop.setdefault(crop_id, []).append(e)
    national = {}
    for crop_id in sorted(per_crop):
        entries = per_crop[crop_id]
        national[crop_id] = {
            "yield_q_per_acre": round(statistics.median(e["yield_q_per_acre"] for e in entries), 2),
            "price_per_q": round(statistics.median(e["price_per_q"] for e in entries)),
            "cost_per_acre": round(statistics.median(e["cost_per_acre"] for e in entries)),
            "year": Counter(e["year"] for e in entries).most_common(1)[0][0],
            "basis": "national_median",
            "n_states": len(entries),
        }
    return {"by_state": by_state, "national": national, "source": SOURCE}


def _pick(samples: dict[str, float], crops: list[dict]) -> list[dict]:
    """The kharif crop and then the rabi crop with the largest sample, the rabi one not repeating the kharif."""
    order = {c["id"]: i for i, c in enumerate(crops)}
    seasons = {c["id"]: c["seasons"] for c in crops}
    picks: list[dict] = []
    for season in ("kharif", "rabi"):
        taken = {p["crop_id"] for p in picks}
        candidates = [c for c in samples if season in seasons.get(c, []) and c not in taken]
        if candidates:
            best = max(candidates, key=lambda c: (samples[c], -order[c]))
            picks.append({"season": season, "crop_id": best})
    return picks


def build_example_rotations(rows: list[dict], crops: list[dict]) -> dict:
    """Example crops per state: the kharif and rabi crops most often surveyed (`num_holdings_sample`)."""
    selectable = {c["id"] for c in crops if c["selectable"]}
    by_state_samples: dict[str, dict[str, float]] = {}
    for (state, crop_id), r in _latest_rows(rows).items():
        if crop_id in selectable:
            by_state_samples.setdefault(state, {})[crop_id] = _number(r.get("num_holdings_sample")) or 0.0
    national_samples: dict[str, float] = {}
    for samples in by_state_samples.values():
        for crop_id, n in samples.items():
            national_samples[crop_id] = national_samples.get(crop_id, 0.0) + n
    return {
        "by_state": {state: _pick(s, crops) for state, s in sorted(by_state_samples.items())},
        "national": _pick(national_samples, crops),
    }
