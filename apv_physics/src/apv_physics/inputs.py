"""Inputs to the physics engine: module, layout, losses and weather, with their limits (design spec §5.1)."""

import math
from dataclasses import dataclass
from enum import StrEnum

import numpy as np

MIN_TRACKER_EDGE_CLEARANCE_M = 0.3


def _check(name: str, value: float, lo: float, hi: float) -> None:
    if not (isinstance(value, int | float) and math.isfinite(value) and lo <= value <= hi):
        raise ValueError(f"{name} must be within [{lo}, {hi}], got {value!r}")


class Kind(StrEnum):
    FIXED = "fixed"
    TRACKER = "tracker"
    VERTICAL = "vertical"


@dataclass(frozen=True)
class Module:
    efficiency: float
    bifaciality: float
    temp_coeff_per_c: float

    def __post_init__(self) -> None:
        _check("efficiency", self.efficiency, 0.15, 0.25)
        _check("bifaciality", self.bifaciality, 0.0, 0.95)
        _check("temp_coeff_per_c", self.temp_coeff_per_c, -0.005, -0.002)


BIFACIAL = Module(0.225, 0.80, -0.0030)
MONOFACIAL = Module(0.210, 0.0, -0.0035)


@dataclass(frozen=True)
class Layout:
    """A panel layout. Only the fields that apply to `kind` are validated and used.

    `height_m` is the lower panel edge above the ground for fixed and vertical layouts, and the axis height
    for trackers. `collector_width_m` is the panel surface width across the row. `azimuth_deg` left as None
    means south (180) for fixed rows and east (90) for vertical rows, which then face east and west.
    """

    kind: Kind
    module: Module
    height_m: float
    collector_width_m: float
    tilt_deg: float = 0.0
    azimuth_deg: float | None = None
    max_angle_deg: float = 55.0
    unfarmed_strip_m: float = 1.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", Kind(self.kind))
        if self.azimuth_deg is None:
            object.__setattr__(self, "azimuth_deg", 90.0 if self.kind is Kind.VERTICAL else 180.0)
        _check("height_m", self.height_m, 0.5, 6.0)
        _check("collector_width_m", self.collector_width_m, 0.5, 10.0)
        if self.kind is Kind.FIXED:
            _check("tilt_deg", self.tilt_deg, 0.0, 40.0)
            _check("azimuth_deg", self.azimuth_deg, 90.0, 270.0)
        elif self.kind is Kind.VERTICAL:
            _check("azimuth_deg", self.azimuth_deg, 90.0, 270.0)
            _check("unfarmed_strip_m", self.unfarmed_strip_m, 0.0, 3.0)
        else:
            _check("max_angle_deg", self.max_angle_deg, 30.0, 60.0)
            edge = self.height_m - self.collector_width_m / 2 * math.sin(math.radians(self.max_angle_deg))
            if edge < MIN_TRACKER_EDGE_CLEARANCE_M:
                raise ValueError(
                    f"height_m is too low for this tracker: the lower panel edge would be {edge:.2f} m above "
                    f"the ground at full turn (minimum {MIN_TRACKER_EDGE_CLEARANCE_M} m)"
                )

    @property
    def center_height_m(self) -> float:
        """Height of the row centre above the ground."""
        if self.kind is Kind.FIXED:
            return self.height_m + self.collector_width_m / 2 * math.sin(math.radians(self.tilt_deg))
        if self.kind is Kind.VERTICAL:
            return self.height_m + self.collector_width_m / 2
        return self.height_m


@dataclass(frozen=True)
class Losses:
    """Fixed system losses (design spec §5.3). Downtime and degradation are finance inputs, not applied here."""

    soiling: float = 0.04
    mismatch: float = 0.01
    dc_wiring: float = 0.015
    connections: float = 0.005
    ac_wiring: float = 0.015
    inverter_efficiency: float = 0.98
    dc_ac_ratio: float = 1.25
    rear_shading: float = 0.05
    albedo: float = 0.20

    def __post_init__(self) -> None:
        for name in ("soiling", "mismatch", "dc_wiring", "connections", "ac_wiring", "rear_shading"):
            _check(name, getattr(self, name), 0.0, 0.5)
        _check("inverter_efficiency", self.inverter_efficiency, 0.5, 1.0)
        _check("dc_ac_ratio", self.dc_ac_ratio, 0.5, 3.0)
        _check("albedo", self.albedo, 0.0, 1.0)

    @property
    def dc_factor(self) -> float:
        return (1 - self.soiling) * (1 - self.mismatch) * (1 - self.dc_wiring) * (1 - self.connections)

    @property
    def ac_factor(self) -> float:
        return 1 - self.ac_wiring


# physical range of each hourly array; a value outside it means a corrupt or mislabelled weather file
_ARRAY_RANGES: dict[str, tuple[float, float]] = {
    "ghi": (0.0, 2000.0),  # W/m2
    "dni": (0.0, 2000.0),
    "dhi": (0.0, 2000.0),
    "temp_air": (-90.0, 70.0),  # deg C
    "wind_speed": (0.0, 100.0),  # m/s
    "zenith": (0.0, 90.0),  # degrees: daylight hours only
    "azimuth": (0.0, 360.0),
    "dni_extra": (1200.0, 1500.0),  # W/m2: the solar constant through the year
}


@dataclass(frozen=True)
class Weather:
    """Hourly weather and sun position for one district point (daylight hours of a typical year)."""

    month: np.ndarray
    ghi: np.ndarray
    dni: np.ndarray
    dhi: np.ndarray
    temp_air: np.ndarray
    wind_speed: np.ndarray
    zenith: np.ndarray
    azimuth: np.ndarray
    dni_extra: np.ndarray
    latitude: float
    longitude: float
    elevation_m: float
    optimum_tilt_deg: float

    def __post_init__(self) -> None:
        month = np.array(self.month)
        if month.ndim != 1 or month.size < 1:
            raise ValueError("month must be a 1-D array with at least one hour")
        if (
            not np.all(np.isfinite(month))
            or np.any(month < 1)
            or np.any(month > 12)
            or np.any(month % 1 != 0)
        ):
            raise ValueError("month must hold whole numbers within 1-12")
        month = month.astype(np.int8)
        month.setflags(write=False)
        object.__setattr__(self, "month", month)
        for name, (lo, hi) in _ARRAY_RANGES.items():
            arr = np.array(getattr(self, name), dtype=float)
            if arr.shape != month.shape:
                raise ValueError(f"{name} must have the same length as month ({month.size})")
            if not np.all(np.isfinite(arr)):
                raise ValueError(f"{name} must be finite")
            if np.any(arr < lo) or np.any(arr > hi):
                raise ValueError(f"{name} must be within [{lo}, {hi}]")
            arr.setflags(write=False)
            object.__setattr__(self, name, arr)
        for name in ("latitude", "longitude", "elevation_m", "optimum_tilt_deg"):
            value = float(getattr(self, name))
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
            object.__setattr__(self, name, value)
