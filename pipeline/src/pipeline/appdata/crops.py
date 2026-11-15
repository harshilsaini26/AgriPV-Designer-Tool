"""The research crops with their draft shade-response parameters and evidence (D16)."""

SEASON_ORDER = ("kharif", "rabi", "zaid")
_SEASON_WORDS = {"kharif": "kharif", "rabi": "rabi", "summer": "zaid", "zaid": "zaid"}
_NAMES = {
    "gram": "Gram (chickpea)",
    "mustard": "Rapeseed & mustard",
    "bajra": "Bajra (pearl millet)",
    "moong": "Moong (green gram)",
    "tur": "Tur (pigeon pea)",
    "jowar": "Jowar (sorghum)",
    "urad": "Urad (black gram)",
    "guar": "Guar (cluster bean)",
    "sesame": "Sesame (til)",
}
SENSITIVE_K = 1.3
TOLERANT_K = 0.9


def _seasons(text: str) -> list[str]:
    words = {_SEASON_WORDS[w.strip()] for w in text.split(",") if w.strip() in _SEASON_WORDS}
    return [s for s in SEASON_ORDER if s in words]


def _range(row: dict, prefix: str) -> dict | None:
    values = [row[f"{prefix}_{suffix}"].strip() for suffix in ("low", "central", "high")]
    if not all(values):
        return None
    low, central, high = (float(v) for v in values)
    return {"pessimistic": low, "central": central, "optimistic": high}


def _citations(study_ids: str, bibliography: dict[str, str]) -> list[str]:
    out = []
    for raw in study_ids.split(";"):
        study = raw.strip().split(":")[0]
        if study and study in bibliography and bibliography[study] not in out:
            out.append(bibliography[study])
    return out


def build_crops(param_rows: list[dict], bibliography_rows: list[dict]) -> list[dict]:
    bibliography = {r["study_id"]: r["citation"] for r in bibliography_rows}
    out = []
    for r in param_rows:
        crop_id = r["crop"].strip()
        seasons = _seasons(r["seasons"])
        l_t, k = _range(r, "lt"), _range(r, "k")
        grade = r["grade"].strip()
        if k is None:
            tolerance = "neutral"
        elif k["central"] >= SENSITIVE_K:
            tolerance = "sensitive"
        elif k["central"] <= TOLERANT_K:
            tolerance = "tolerant"
        else:
            tolerance = "neutral"
        reason = None
        if not seasons:
            reason = "whole-year crop: the model works by season"
        elif grade == "D" or l_t is None or k is None:
            reason = "not enough evidence (grade D)"
        out.append(
            {
                "id": crop_id,
                "name": _NAMES.get(crop_id, crop_id.capitalize()),
                "seasons": seasons,
                "tolerance": tolerance,
                "l_t": l_t,
                "k": k,
                "grade": grade,
                "n_studies": int(r["n_studies"] or 0),
                "n_indian_studies": int(r["n_indian_studies"] or 0),
                "citations": _citations(r["study_ids"], bibliography),
                "notes": r["notes"].strip(),
                "selectable": reason is None,
                "not_selectable_reason": reason,
            }
        )
    return out
