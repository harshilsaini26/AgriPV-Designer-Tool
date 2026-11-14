"""Stored results for three district-and-layout pairs, so accidental changes to the engine are caught.

To regenerate after an intended change: set APV_PHYSICS_WRITE_SNAPSHOTS=1, run this file, read the diff.
"""

import csv
import os
from pathlib import Path

import numpy as np
import pytest

from apv_physics import BIFACIAL, Kind, Layout, load_weather, simulate

DATA = Path(__file__).parent / "data"
ROW = 5  # GCR 0.25
CASES = {
    "jodhpur_fixed_3m": ("107_jodhpur", Layout(Kind.FIXED, BIFACIAL, 3.0, 4.56, tilt_deg=25.0)),
    "ernakulam_tracker_2.5m": ("555_ernakulam", Layout(Kind.TRACKER, BIFACIAL, 2.5, 2.28)),
    "leh_vertical": ("9_leh_ladakh", Layout(Kind.VERTICAL, BIFACIAL, 0.8, 2.27, azimuth_deg=90.0)),
}
COLUMNS = ["month", "energy_kwh_per_kwp", "light_fraction", "light_darkest_tenth"]


@pytest.mark.parametrize("name", list(CASES))
def test_snapshot(name):
    district, layout = CASES[name]
    r = simulate(load_weather(DATA / f"{district}.npz"), layout)
    got = np.column_stack(
        [
            np.arange(1, 13),
            r.table.energy_kwh_per_kwp[ROW],
            r.table.light_fraction[ROW],
            r.light_darkest_tenth[ROW],
        ]
    )
    path = DATA / "snapshots" / f"{name}.csv"
    if os.environ.get("APV_PHYSICS_WRITE_SNAPSHOTS") == "1":
        path.parent.mkdir(exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(COLUMNS)
            w.writerows([int(row[0]), *(f"{v:.6f}" for v in row[1:])] for row in got)
    with path.open(encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    assert rows[0] == COLUMNS
    np.testing.assert_allclose(got, np.array(rows[1:], dtype=float), rtol=1e-5, atol=1e-6)
