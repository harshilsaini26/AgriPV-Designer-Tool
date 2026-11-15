"""Finance defaults, structure presets and the sources register for the app (model-slice spec §5)."""

import re

# Not researched yet (data requirement D21): placeholders the interface labels as assumptions.
ASSUMPTIONS: dict[str, float] = {
    "debt_share": 0.70,
    "interest_rate": 0.10,
    "loan_years": 15,
    "discount_rate": 0.09,
    "degradation": 0.005,
    "availability": 0.99,
    "crop_inflation": 0.05,
    "target_irr": 0.12,
    "lease_per_acre_year": 40000,
    "lease_escalation": 0.05,
}

# Input limits of the physics engine (live-physics design §5.1) and the farmable fraction.
LIMITS: dict[str, list[float]] = {
    "tilt_deg": [0.0, 40.0],
    "azimuth_deg": [90.0, 270.0],
    "max_angle_deg": [30.0, 60.0],
    "height_m": [0.5, 6.0],
    "collector_width_m": [0.5, 10.0],
    "unfarmed_strip_m": [0.0, 3.0],
    "efficiency": [0.15, 0.25],
    "bifaciality": [0.0, 0.95],
    "temp_coeff_per_c": [-0.005, -0.002],
    "a_farm": [0.5, 1.0],
}

_REFERENCE = "ground_fixed_reference"
_FIXED_TILT_RULE = "optimum_10_25"
_NAMES = {
    "elevated_fixed_2.5m": "Elevated fixed, 2.5 m",
    "elevated_fixed_3m": "Elevated fixed, 3 m",
    "elevated_fixed_4m": "Elevated fixed, 4 m",
    "tracker_2.5m": "Single-axis tracker, 2.5 m",
    "tracker_4m": "Single-axis tracker, 4 m",
    "vertical_bifacial_ew": "Vertical bifacial, east-west",
}

SOURCES: list[dict] = [
    {
        "id": "weather",
        "title": "Typical-year weather for each district",
        "attribution": "PVGIS © European Union (JRC), PVGIS-ERA5 2005–2023; contains modified Copernicus Climate "
        "Change Service information (ERA5); calibrated to Global Solar Atlas 2.0 (Solargis / World Bank Group)",
        "licence": "PVGIS: free use with acknowledgement; ERA5: Copernicus licence; Global Solar Atlas: CC BY 4.0",
        "url": "https://re.jrc.ec.europa.eu/pvg_tools/",
        "used_for": "panel energy and light on the crop",
    },
    {
        "id": "crop_shade",
        "title": "Crop response to shade (draft parameters)",
        "attribution": "Laub, M. et al. (2022), meta-analysis data set, plus the field trials listed with each crop",
        "licence": "CC BY 4.0 (meta-analysis); papers cited, not reproduced",
        "url": "https://github.com/harshilsaini26/AgriPV-Designer-Tool/tree/main/research/09_crop_shade_response",
        "used_for": "yield kept under panels; evidence grades",
    },
    {
        "id": "crop_economics",
        "title": "Cost of cultivation, yield and value by state",
        "attribution": "Directorate of Economics and Statistics, Ministry of Agriculture and Farmers Welfare, "
        "via India Data Portal",
        "licence": "ODC-By",
        "url": "https://indiadataportal.com/",
        "used_for": "crop yield, price and cost defaults (state figures, latest year)",
    },
    {
        "id": "tariffs",
        "title": "PM-KUSUM Component A tariffs",
        "attribution": "State electricity regulatory commission orders, as listed with each tariff",
        "licence": "Public regulatory orders (facts cited)",
        "url": "https://github.com/harshilsaini26/AgriPV-Designer-Tool/tree/main/research/11_finance_policy/kusum",
        "used_for": "default tariff per state",
    },
    {
        "id": "costs",
        "title": "Capital and operating cost benchmarks",
        "attribution": "MPERC order in Petition 13 of 2024 (20 June 2024), with agrivoltaic cost multipliers from "
        "published Indian and international benchmarks",
        "licence": "Public regulatory order (facts cited)",
        "url": "https://mperc.in/",
        "used_for": "cost per kWp and O&M per structure",
    },
    {
        "id": "structures",
        "title": "Structure presets",
        "attribution": "AgriPV Lab presets; land-loss limits from DIN SPEC 91434:2021-05 via Fraunhofer ISE (2022), "
        "Agrivoltaics: Opportunities for Agriculture and the Energy Transition",
        "licence": "Cited facts; presets partly assumed",
        "url": "https://github.com/harshilsaini26/AgriPV-Designer-Tool/tree/main/research/12_structures_technology",
        "used_for": "layouts and farmable fraction",
    },
    {
        "id": "modules",
        "title": "Module parameters",
        "attribution": "Manufacturer datasheets (Polycab, Onix Renewable, Emmvee)",
        "licence": "Cited facts",
        "url": "https://github.com/harshilsaini26/AgriPV-Designer-Tool/tree/main/research/12_structures_technology",
        "used_for": "efficiency, bifaciality, temperature coefficient",
    },
    {
        "id": "districts",
        "title": "District names and codes",
        "attribution": "Local Government Directory (Ministry of Panchayati Raj); boundaries via Bharatlas",
        "licence": "Government Open Data Licence – India",
        "url": "https://lgdirectory.gov.in/",
        "used_for": "district list and search",
    },
    {
        "id": "pvlib",
        "title": "Physics engine",
        "attribution": "View-factor and irradiance code adapted from pvlib-python 0.16.1",
        "licence": "BSD 3-Clause",
        "url": "https://github.com/pvlib/pvlib-python",
        "used_for": "panel irradiance and ground light",
    },
]


def _num(text: str) -> float:
    """The first number in a cell such as '80 (±10)' or '-0.30 to -0.33'."""
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if match is None:
        raise ValueError(f"no number in {text!r}")
    return float(match.group())


def _int(text: str) -> int:
    return round(float(text))


def build_finance_defaults(tariff_rows: list[dict], capex_rows: list[dict]) -> dict:
    tariffs, fallback = {}, None
    for r in tariff_rows:
        if r["state"] == "NATIONAL_FALLBACK":
            fallback = {"tariff_per_kwh": float(r["tariff_inr_per_kwh"]), "flag": "state_fallback"}
            continue
        tariffs[r["state"]] = {
            "tariff_per_kwh": float(r["tariff_inr_per_kwh"]),
            "order": r["regulator_order"],
            "order_date": r["order_date"],
            "status": r["status"],
            "flag": "state",
        }
    if fallback is None:
        raise ValueError("tariff table has no NATIONAL_FALLBACK row")
    ref = next(r for r in capex_rows if r["preset_id"] == _REFERENCE)
    return {
        "tariffs": tariffs,
        "national_fallback": fallback,
        "base_capex_per_kwp": {
            case: _int(ref[f"capex_inr_per_kwp_dc_{case}"]) for case in ("central", "low", "high")
        },
        "base_om_per_kwp_year": {
            case: _int(ref[f"om_inr_per_kwp_dc_yr1_{case}"]) for case in ("central", "low", "high")
        },
        "om_escalation": round(float(ref["om_escalation_pct_per_yr"]) / 100, 4),
        "price_year": int(ref["price_year"]),
        "assumptions": {name: {"value": value, "flag": "assumption"} for name, value in ASSUMPTIONS.items()},
    }


def _kind(preset_id: str) -> str:
    if preset_id.startswith("tracker"):
        return "tracker"
    if preset_id.startswith("vertical"):
        return "vertical"
    return "fixed"


def build_structures(preset_rows: list[dict], module_rows: list[dict], capex_rows: list[dict]) -> dict:
    capex = {r["preset_id"]: r for r in capex_rows}
    presets, cost_points = [], {"fixed": [], "tracker": [], "vertical": []}
    for r in preset_rows:
        preset_id = r["preset_id"]
        if preset_id == _REFERENCE:
            continue
        kind = _kind(preset_id)
        height = float(r["hub_height_m"] if kind == "tracker" else r["clearance_m"])
        multiplier = float(capex[preset_id]["capex_multiplier_central"])
        presets.append(
            {
                "id": preset_id,
                "name": _NAMES.get(preset_id, preset_id),
                "kind": kind,
                "tilt_rule": _FIXED_TILT_RULE if kind == "fixed" else None,
                "azimuth_deg": {"fixed": 180.0, "vertical": 90.0}.get(kind),
                "height_m": height,
                "collector_width_m": float(r["collector_width_m"]),
                "max_angle_deg": 55.0 if kind == "tracker" else None,
                "unfarmed_strip_m": 1.0 if kind == "vertical" else 0.0,
                "module": "bifacial",
                "a_farm": {case: float(r[f"a_farm_{case}"]) for case in ("central", "low", "high")},
                "capex_multiplier": multiplier,
                "om_multiplier": float(capex[preset_id]["om_multiplier"]),
                "machinery": r["machinery_pass"],
                "din_category": r["din_spec_91434_category"],
            }
        )
        cost_points[kind].append([height, multiplier])
    modules = {}
    for r in module_rows:
        modules[r["module_option"]] = {
            "efficiency": round(_num(r["efficiency_pct_default"]) / 100, 4),
            "bifaciality": round(_num(r["bifaciality_pct"]) / 100, 4),
            "temp_coeff_per_c": round(_num(r["temp_coeff_pmax_pct_per_c"]) / 100, 5),
        }
    return {
        "presets": presets,
        "modules": modules,
        "cost_points": {kind: sorted(points) for kind, points in cost_points.items()},
        "limits": LIMITS,
    }
