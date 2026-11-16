"""Request and response models: the API contract (model-slice spec §6)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Season = Literal["kharif", "rabi", "zaid"]


class Health(BaseModel):
    status: str
    weather_packs: int
    python: str
    data_version: str


class CaseValues(BaseModel):
    """Shade-response parameter for the three cases."""

    pessimistic: float
    central: float
    optimistic: float


class Band(BaseModel):
    """A value with its low-high range."""

    central: float
    low: float
    high: float


class Crop(BaseModel):
    id: str
    name: str
    seasons: list[Season]
    tolerance: str
    l_t: CaseValues | None
    k: CaseValues | None
    grade: str
    n_studies: int
    n_indian_studies: int
    citations: list[str]
    notes: str
    selectable: bool
    not_selectable_reason: str | None


class Preset(BaseModel):
    id: str
    name: str
    kind: Literal["fixed", "tracker", "vertical"]
    tilt_rule: str | None
    azimuth_deg: float | None
    height_m: float
    collector_width_m: float
    max_angle_deg: float | None
    unfarmed_strip_m: float
    module: str
    a_farm: Band
    capex_multiplier: float
    om_multiplier: float
    machinery: str
    din_category: str


class ModuleSpec(BaseModel):
    efficiency: float
    bifaciality: float
    temp_coeff_per_c: float


class Assumption(BaseModel):
    value: float
    flag: Literal["assumption"]


class Source(BaseModel):
    id: str
    title: str
    attribution: str
    licence: str
    url: str
    used_for: str


class Policy(BaseModel):
    default: float
    min: float
    max: float
    step: float


class Meta(BaseModel):
    data_version: str
    preview_notice: str
    presets: list[Preset]
    modules: dict[str, ModuleSpec]
    limits: dict[str, list[float]]
    crops: list[Crop]
    seasons: list[Season]
    policy: Policy
    retention_bases: list[Literal["per_acre_of_land", "per_cropped_area"]]
    business_models: list[Literal["kusum_a", "lease"]]
    assumptions: dict[str, Assumption]
    sources: list[Source]


class DistrictListItem(BaseModel):
    id: str
    name: str
    state: str


class Tariff(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    tariff_per_kwh: float
    flag: Literal["state", "state_fallback"]
    order: str | None = None
    order_date: str | None = None
    status: str | None = None


class Economics(BaseModel):
    yield_q_per_acre: float
    price_per_q: float
    cost_per_acre: float
    year: str
    basis: Literal["state", "national_median"]
    n_states: int | None = None


class RotationEntry(BaseModel):
    season: Season
    crop_id: str


class ExampleRotation(BaseModel):
    basis: Literal["state", "national"]
    crops: list[RotationEntry]


class District(BaseModel):
    id: str
    lgd: str
    name: str
    state: str
    lat: float
    lon: float
    elevation_m: float
    optimum_tilt_deg: float
    default_tilt_deg: float
    tariff: Tariff
    economics: dict[str, Economics]
    example_rotation: ExampleRotation


# ---------------------------------------------------------------- the sweep (spec §6)


class ModuleIn(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    efficiency: float
    bifaciality: float
    temp_coeff_per_c: float


class LayoutIn(BaseModel):
    """A structure: a preset to start from, and any fields the user changed."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    preset_id: str | None = None
    kind: Literal["fixed", "tracker", "vertical"]
    tilt_deg: float | None = None
    azimuth_deg: float | None = None
    height_m: float | None = None
    collector_width_m: float | None = None
    max_angle_deg: float | None = None
    unfarmed_strip_m: float | None = None
    module: ModuleIn | None = None


class EconomicsIn(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    yield_q_per_acre: float = Field(ge=0)
    price_per_q: float = Field(ge=0)
    cost_per_acre: float = Field(ge=0)


class RotationIn(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    season: Season
    crop_id: str
    economics: EconomicsIn | None = None


class FinanceIn(BaseModel):
    """Overrides only; anything left out takes the state's, the structure's or the assumed default."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    capex_per_kwp: float | None = None
    om_per_kwp_year: float | None = None
    om_escalation: float | None = None
    tariff_per_kwh: float | None = None
    degradation: float | None = None
    availability: float | None = None
    debt_share: float | None = None
    interest_rate: float | None = None
    loan_years: int | None = None
    discount_rate: float | None = None
    crop_inflation: float | None = None
    lease_per_acre_year: float | None = None
    lease_escalation: float | None = None
    target_irr: float | None = None


class SweepRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    district_id: str
    business_model: Literal["kusum_a", "lease"]
    layout: LayoutIn
    a_farm: float | None = Field(default=None, ge=0.5, le=1.0)
    rotation: list[RotationIn]
    finance: FinanceIn = Field(default_factory=FinanceIn)
    policy_limit: float = Field(default=0.8, ge=0.5, le=1.0)
    retention_basis: Literal["per_acre_of_land", "per_cropped_area"] = "per_acre_of_land"
    land_acres: float | None = Field(default=None, gt=0)


class RangeOut(BaseModel):
    """A result for the three cases. Named by case, not by size: for a cost-like figure such as payback the
    pessimistic value is the larger one. Null where a value is undefined (e.g. no IRR)."""

    pessimistic: float | None
    central: float | None
    optimistic: float | None


class SeasonLight(BaseModel):
    mean: list[float]
    darkest_tenth: list[float]


class NoticeOut(BaseModel):
    code: str
    message: str
    gcr: float | None
    gcrs: list[float]


class InputUsed(BaseModel):
    name: str
    value: float | int | str | None
    flag: Literal[
        "state",
        "national_median",
        "state_fallback",
        "preset",
        "interpolated",
        "outside_benchmark_range",
        "assumption",
        "user",
    ]
    source: str
    year: int | None


class SweepResponse(BaseModel):
    gcr: list[float]
    metrics: dict[str, list[RangeOut]]
    retention: dict[str, list[RangeOut]]
    retention_basis: Literal["per_acre_of_land", "per_cropped_area"]
    light: dict[str, SeasonLight]
    clear_gap_m: list[float | None]
    allowed_gcr: RangeOut
    outside_policy: list[bool]
    baseline_farm_income: float
    notices: list[NoticeOut]
    inputs_used: list[InputUsed]
    custom_layout: bool
    data_version: str
    engine_ms: float
