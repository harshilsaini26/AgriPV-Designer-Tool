"""Pre-computed physics lookup for one district and structure, plus land-use helpers (spec §12.1–12.2)."""

from dataclasses import dataclass

import numpy as np

from apv_core.constants import ACRE_M2, GCR_GRID

_SHAPE = (len(GCR_GRID), 12)


@dataclass(frozen=True)
class Structure:
    id: str
    a_farm: float
    module_efficiency: float

    def __post_init__(self) -> None:
        if not 0.0 < self.a_farm <= 1.0:
            raise ValueError(f"structure {self.id!r}: a_farm must be in (0, 1]")
        if not 0.0 < self.module_efficiency < 0.4:
            raise ValueError(f"structure {self.id!r}: module_efficiency must be in (0, 0.4)")


@dataclass(frozen=True)
class PhysicsTable:
    """Monthly energy (kWh/kWp) and ground light fraction per GCR_GRID row; row 0 is the open field."""

    energy_kwh_per_kwp: np.ndarray
    light_fraction: np.ndarray
    ref_energy_kwh_per_acre: float

    def __post_init__(self) -> None:
        energy = np.array(self.energy_kwh_per_kwp, dtype=float)
        light = np.array(self.light_fraction, dtype=float)
        if energy.shape != _SHAPE or light.shape != _SHAPE:
            raise ValueError(f"physics arrays must have shape {_SHAPE}")
        if np.any(light < 0.0) or np.any(light > 1.0):
            raise ValueError("light_fraction must be within [0, 1]")
        if not np.all(light[0] == 1.0):
            raise ValueError("light_fraction row 0 (GCR 0, open field) must be all 1.0")
        if np.any(energy < 0.0):
            raise ValueError("energy_kwh_per_kwp must be >= 0")
        if not np.all(energy[0] == 0.0):
            raise ValueError("energy_kwh_per_kwp row 0 (GCR 0, no panels) must be all 0.0")
        if not self.ref_energy_kwh_per_acre > 0.0:
            raise ValueError("ref_energy_kwh_per_acre must be > 0")
        energy.setflags(write=False)
        light.setflags(write=False)
        object.__setattr__(self, "energy_kwh_per_kwp", energy)
        object.__setattr__(self, "light_fraction", light)


def kwp_per_acre(gcr: float, module_efficiency: float) -> float:
    return gcr * ACRE_M2 * module_efficiency


def farmable_fraction(gcr: float, structure: Structure) -> float:
    return 1.0 if gcr == 0.0 else structure.a_farm
