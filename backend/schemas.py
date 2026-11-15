"""Request and response models: the API contract (model-slice spec §6)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

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
    model_config = ConfigDict(extra="forbid")

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
