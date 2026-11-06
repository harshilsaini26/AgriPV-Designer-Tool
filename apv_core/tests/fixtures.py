"""Synthetic, test-only builders. None of these values are real district data."""

import numpy as np

from apv_core.constants import GCR_GRID, Season
from apv_core.crops import CropParams, EvidenceGrade
from apv_core.farm import CropEconomics, SeasonCrop
from apv_core.physics import PhysicsTable, Structure
from apv_core.ranges import Range


def synthetic_physics() -> PhysicsTable:
    energy = np.zeros((len(GCR_GRID), 12))
    light = np.ones((len(GCR_GRID), 12))
    bonus = np.array([0.05 if m in (6, 7, 8, 9) else 0.0 for m in range(1, 13)])  # monsoon diffuse light
    for i, g in enumerate(GCR_GRID):
        if i == 0:
            continue
        energy[i, :] = 130.0 * (1 - 0.1 * g)
        light[i, :] = np.clip(1 - 1.2 * g + bonus, 0.0, 1.0)
    return PhysicsTable(energy, light, ref_energy_kwh_per_acre=0.45 * 4046.86 * 0.215 * 1560.0)


def elevated_structure() -> Structure:
    return Structure("elevated-3m-bifacial", a_farm=0.95, module_efficiency=0.215)


def soybean_kharif() -> SeasonCrop:
    crop = CropParams(
        id="soybean",
        name="Soybean",
        seasons=frozenset({Season.KHARIF}),
        tolerance="neutral",
        l_t=Range(0.80, 0.70, 0.60),
        k=Range(1.2, 1.0, 0.8),
        grade=EvidenceGrade.B,
    )
    return SeasonCrop(Season.KHARIF, crop, CropEconomics(4.0, 4600.0, 13000.0))


def onion_rabi() -> SeasonCrop:
    crop = CropParams(
        id="onion",
        name="Onion",
        seasons=frozenset({Season.RABI}),
        tolerance="tolerant",
        l_t=Range(0.65, 0.55, 0.45),
        k=Range(1.0, 0.8, 0.6),
        grade=EvidenceGrade.C,
    )
    return SeasonCrop(Season.RABI, crop, CropEconomics(80.0, 1500.0, 60000.0))
