"""Turn a sweep request into model inputs, run the physics and the model, and shape the response (spec §6).

Every default the service applies is reported in `inputs_used` with where it came from.
"""

import bisect
import math
import time
from functools import lru_cache

import numpy as np
from apv_core.crops import season_light

from apv_core import (
    BusinessModel,
    CropEconomics,
    CropParams,
    EvidenceGrade,
    FinanceInputs,
    Range,
    RetentionBasis,
    Season,
    SeasonCrop,
    Structure,
    SweepInputs,
    run_sweep,
)
from apv_physics import Kind, Layout, Module, PhysicsResult, load_weather, simulate
from backend._paths import REPO_ROOT  # noqa: F401  (puts apv_core and apv_physics on the path)
from backend.data import (
    AppData,
    default_tilt_deg,
    economics_for,
    load_app_data,
    tariff_for,
    weather_path,
)
from backend.schemas import FinanceIn, LayoutIn, RotationIn, SweepRequest

SRC_USER = "entered by the user"
SRC_PRESET = "structure preset"
SRC_TILT = "optimum tilt limited to 10-25 degrees"
SRC_COSTS = "MPERC 2024 cost norms x structure multiplier"
SRC_OM_ESCALATION = "CERC RE tariff regulations 2024, as used by MPERC 2024"
SRC_ECONOMICS = "DES cost of cultivation"
SRC_FALLBACK_TARIFF = "national fallback: median of the state PM-KUSUM A tariffs"
SRC_ASSUMPTION = "assumption"
COSTS_YEAR = 2024

# Defaults when no preset is named (spec §6)
KIND_DEFAULTS = {
    "fixed": {"height_m": 3.0, "collector_width_m": 4.56, "azimuth_deg": 180.0},
    "tracker": {"height_m": 2.5, "collector_width_m": 2.28, "max_angle_deg": 55.0},
    "vertical": {"height_m": 0.8, "collector_width_m": 2.27, "azimuth_deg": 90.0, "unfarmed_strip_m": 1.0},
}
KIND_A_FARM = {"fixed": 0.92, "tracker": 0.90, "vertical": 0.88}
KIND_OM_MULTIPLIER = {"fixed": 1.1, "tracker": 1.2, "vertical": 1.0}
LAYOUT_FIELDS = {
    "fixed": ("tilt_deg", "azimuth_deg", "height_m", "collector_width_m"),
    "tracker": ("max_angle_deg", "height_m", "collector_width_m"),
    "vertical": ("azimuth_deg", "height_m", "collector_width_m", "unfarmed_strip_m"),
}


class InputError(ValueError):
    """A request value the model cannot use; `loc` names it inside the request body."""

    def __init__(self, loc: tuple, message: str) -> None:
        super().__init__(message)
        self.loc = loc
        self.message = message


def _used(name: str, value, flag: str, source: str, year: int | None = None) -> dict:
    return {"name": name, "value": value, "flag": flag, "source": source, "year": year}


def _year(text: str | None) -> int | None:
    digits = (text or "")[:4]
    return int(digits) if digits.isdigit() else None


def cost_multiplier(kind: str, height_m: float, cost_points: dict) -> tuple[float, str]:
    """Capital cost multiplier for a structure kind at a height, from the benchmark points (spec §5)."""
    points = sorted(cost_points[kind])
    heights = [h for h, _ in points]
    for h, m in points:
        if math.isclose(h, height_m):
            return m, "preset"
    if height_m < heights[0]:
        return points[0][1], "outside_benchmark_range"
    if height_m > heights[-1]:
        return points[-1][1], "outside_benchmark_range"
    i = bisect.bisect_left(heights, height_m)
    (h0, m0), (h1, m1) = points[i - 1], points[i]
    return m0 + (m1 - m0) * (height_m - h0) / (h1 - h0), "interpolated"


def _preset(app: AppData, layout: LayoutIn) -> dict | None:
    if layout.preset_id is None:
        return None
    preset = next((p for p in app.structures["presets"] if p["id"] == layout.preset_id), None)
    if preset is None:
        raise InputError(("layout", "preset_id"), f"unknown structure preset {layout.preset_id!r}")
    if preset["kind"] != layout.kind:
        raise InputError(("layout", "kind"), f"preset {layout.preset_id!r} is a {preset['kind']} structure")
    return preset


def resolve_layout(layout: LayoutIn, district: dict, app: AppData) -> tuple[Layout, list[dict], bool]:
    """The physics layout, the layout entries of `inputs_used`, and whether the user changed the preset."""
    preset = _preset(app, layout)
    kind = layout.kind
    base = dict(KIND_DEFAULTS[kind])
    if preset is not None:
        base.update({k: preset[k] for k in ("height_m", "collector_width_m") if preset[k] is not None})
        for k in ("azimuth_deg", "max_angle_deg"):
            if preset[k] is not None:
                base[k] = preset[k]
        if kind == "vertical":
            base["unfarmed_strip_m"] = preset["unfarmed_strip_m"]
    if kind == "fixed":
        base["tilt_deg"] = default_tilt_deg(district)
    source = SRC_PRESET if preset is not None else f"default for a {kind} structure"

    used, values, custom = [], {}, preset is None
    for name in LAYOUT_FIELDS[kind]:
        requested = getattr(layout, name)
        if requested is not None:
            values[name] = requested
            used.append(_used(f"layout.{name}", requested, "user", SRC_USER))
            custom = custom or not math.isclose(requested, base[name])
        else:
            values[name] = base[name]
            src = SRC_TILT if name == "tilt_deg" else source
            used.append(_used(f"layout.{name}", base[name], "preset", src))

    module_defaults = app.structures["modules"][preset["module"] if preset else "bifacial"]
    if layout.module is not None:
        module_values = layout.module.model_dump()
        custom = True
        flag, src = "user", SRC_USER
    else:
        module_values, flag, src = module_defaults, "preset", SRC_PRESET
    for name, value in module_values.items():
        used.append(_used(f"layout.module.{name}", value, flag, src))

    physics_layout = Layout(
        kind=Kind(kind),
        module=Module(**module_values),
        height_m=values["height_m"],
        collector_width_m=values["collector_width_m"],
        tilt_deg=values.get("tilt_deg", 0.0),
        azimuth_deg=values.get("azimuth_deg"),
        max_angle_deg=values.get("max_angle_deg", 55.0),
        unfarmed_strip_m=values.get("unfarmed_strip_m", 1.0),
    )
    return physics_layout, used, custom


def resolve_finance(
    finance: FinanceIn, district: dict, layout: Layout, preset: dict | None, app: AppData
) -> tuple[FinanceInputs, list[dict]]:
    defaults = app.finance
    multiplier, cost_flag = cost_multiplier(layout.kind.value, layout.height_m, app.structures["cost_points"])
    om_multiplier = preset["om_multiplier"] if preset else KIND_OM_MULTIPLIER[layout.kind.value]
    tariff = tariff_for(app, district["state"])
    if tariff["flag"] == "state":
        tariff_source, tariff_year = tariff["order"], _year(tariff.get("order_date"))
    else:
        tariff_source, tariff_year = SRC_FALLBACK_TARIFF, None

    resolved = {
        "capex_per_kwp": (defaults["base_capex_per_kwp"]["central"] * multiplier, cost_flag, SRC_COSTS, COSTS_YEAR),
        "om_per_kwp_year": (defaults["base_om_per_kwp_year"]["central"] * om_multiplier, "preset", SRC_COSTS, COSTS_YEAR),
        "om_escalation": (defaults["om_escalation"], "preset", SRC_OM_ESCALATION, COSTS_YEAR),
        "tariff_per_kwh": (tariff["tariff_per_kwh"], tariff["flag"], tariff_source, tariff_year),
    }  # fmt: skip
    for name, entry in defaults["assumptions"].items():
        resolved[name] = (entry["value"], "assumption", SRC_ASSUMPTION, None)

    values, used = {}, []
    for name, (value, flag, source, year) in resolved.items():
        requested = getattr(finance, name)
        if requested is not None:
            value, flag, source, year = requested, "user", SRC_USER, None
        values[name] = value
        used.append(_used(f"finance.{name}", value, flag, source, year))
    values["loan_years"] = int(values["loan_years"])
    return FinanceInputs(**values), used


def _crop_params(crop: dict) -> CropParams:
    return CropParams(
        crop["id"],
        crop["name"],
        frozenset(Season(s) for s in crop["seasons"]),
        crop["tolerance"],
        Range(**crop["l_t"]),
        Range(**crop["k"]),
        EvidenceGrade(crop["grade"]),
        citations=tuple(crop["citations"]),
    )


def resolve_rotation(
    rotation: list[RotationIn], district: dict, app: AppData
) -> tuple[tuple[SeasonCrop, ...], list[dict]]:
    if not rotation:
        raise InputError(("rotation",), "add at least one crop")
    seen, out, used = set(), [], []
    for i, entry in enumerate(rotation):
        crop = app.crops.get(entry.crop_id)
        if crop is None:
            raise InputError(("rotation", i, "crop_id"), f"unknown crop {entry.crop_id!r}")
        if not crop["selectable"]:
            raise InputError(
                ("rotation", i, "crop_id"),
                f"{crop['name']} cannot be modelled yet: {crop['not_selectable_reason']}",
            )
        if entry.season not in crop["seasons"]:
            raise InputError(("rotation", i, "season"), f"{crop['name']} is not grown in {entry.season}")
        if entry.season in seen:
            raise InputError(("rotation", i, "season"), f"the rotation already has a {entry.season} crop")
        seen.add(entry.season)

        prefix = f"rotation.{entry.season}.{crop['id']}"
        if entry.economics is not None:
            figures = entry.economics.model_dump()
            flag, source, year, user = "user", SRC_USER, None, True
        else:
            found = economics_for(app, district["state"], crop["id"])
            if found is None:
                raise InputError(
                    ("rotation", i, "economics"),
                    f"no yield, price or cost data for {crop['name']}: enter them",
                )
            figures = {k: found[k] for k in ("yield_q_per_acre", "price_per_q", "cost_per_acre")}
            flag, source, year, user = found["basis"], SRC_ECONOMICS, _year(found["year"]), False
        for name, value in figures.items():
            used.append(_used(f"{prefix}.{name}", value, flag, source, year))
        out.append(
            SeasonCrop(Season(entry.season), _crop_params(crop), CropEconomics(**figures, user_entered=user))
        )
    return tuple(out), used


@lru_cache(maxsize=64)
def physics_for(district_id: str, layout: Layout) -> PhysicsResult:
    """The physics result for a district and layout, kept so a change to crops or finance does not rerun it."""
    return simulate(load_weather(weather_path(district_id)), layout)


def build_sweep_inputs(req: SweepRequest) -> tuple[SweepInputs, PhysicsResult, list[dict], bool]:
    """Resolve every default; raises LookupError for an unknown district and InputError for a bad value."""
    app = load_app_data()
    district = app.districts.get(req.district_id)
    if district is None:
        raise LookupError(req.district_id)
    layout, used, custom = resolve_layout(req.layout, district, app)
    preset = _preset(app, req.layout)
    rotation, rotation_used = resolve_rotation(req.rotation, district, app)
    finance, finance_used = resolve_finance(req.finance, district, layout, preset, app)

    if req.a_farm is not None:
        a_farm = req.a_farm
        used.append(_used("a_farm", a_farm, "user", SRC_USER))
    else:
        a_farm = preset["a_farm"]["central"] if preset else KIND_A_FARM[req.layout.kind]
        used.append(
            _used(
                "a_farm",
                a_farm,
                "preset",
                SRC_PRESET if preset else f"default for a {req.layout.kind} structure",
            )
        )

    physics = physics_for(req.district_id, layout)
    inputs = SweepInputs(
        physics=physics.table,
        structure=Structure(
            req.layout.preset_id or "custom", a_farm=a_farm, module_efficiency=layout.module.efficiency
        ),
        rotation=rotation,
        finance=finance,
        business_model=BusinessModel(req.business_model),
        policy_limit=req.policy_limit,
        retention_basis=RetentionBasis(req.retention_basis),
        land_acres=req.land_acres,
    )
    return inputs, physics, used + rotation_used + finance_used, custom


def _finite(x) -> float | None:
    if x is None:
        return None
    x = float(x)
    return x if math.isfinite(x) else None


def _range(r: Range) -> dict:
    return {"low": _finite(r.pessimistic), "central": _finite(r.central), "high": _finite(r.optimistic)}


def run_sweep_request(req: SweepRequest) -> dict:
    t0 = time.perf_counter()
    inputs, physics, used, custom = build_sweep_inputs(req)
    result = run_sweep(inputs)
    light = {}
    for sc in inputs.rotation:
        season = sc.season
        light[season.value] = {
            "mean": [round(float(v), 4) for v in season_light(physics.table.light_fraction, season)],
            "darkest_tenth": [round(float(v), 4) for v in season_light(physics.light_darkest_tenth, season)],
        }
    return {
        "gcr": list(result.gcr),
        "metrics": {key: [_range(r) for r in ranges] for key, ranges in result.metrics.items()},
        "retention": {
            season.value: [_range(r) for r in ranges] for season, ranges in result.retention.items()
        },
        "retention_basis": result.retention_basis.value,
        "light": light,
        "clear_gap_m": [_finite(v) for v in np.asarray(physics.clear_gap_m)],
        "allowed_gcr": _range(result.allowed_gcr),
        "outside_policy": list(result.outside_policy),
        "baseline_farm_income": float(result.baseline_farm_income),
        "notices": [
            {"code": n.code.value, "message": n.message, "gcr": n.gcr, "gcrs": list(n.gcrs)}
            for n in result.notices
        ],
        "inputs_used": used,
        "custom_layout": custom,
        "data_version": load_app_data().manifest["data_version"],
        "engine_ms": round((time.perf_counter() - t0) * 1000, 1),
    }
