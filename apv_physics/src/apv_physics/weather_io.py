"""The weather pack format: one compressed .npz file per district (design spec §6).

Arrays are stored as scaled integers to keep each pack small. `meta` is a JSON string.
"""

import json
from typing import Any

import numpy as np

from apv_physics.inputs import Weather

PACK_VERSION = 1

# array name -> (stored dtype, scale): stored = round(value * scale)
_FIELDS: dict[str, tuple[type, float]] = {
    "ghi": (np.int16, 10.0),
    "dni": (np.int16, 10.0),
    "dhi": (np.int16, 10.0),
    "dni_extra": (np.int16, 10.0),
    "temp_air": (np.int16, 10.0),
    "wind_speed": (np.int16, 10.0),
    "zenith": (np.int16, 100.0),
    "azimuth": (np.uint16, 100.0),
}
_SCALARS = ("latitude", "longitude", "elevation_m", "optimum_tilt_deg")


def save_weather(weather: Weather, meta: dict[str, Any], file: Any) -> None:
    """Write a weather pack. `file` is a path or a binary file object."""
    arrays: dict[str, np.ndarray] = {"month": weather.month.astype(np.int8)}
    for name, (dtype, scale) in _FIELDS.items():
        scaled = np.rint(getattr(weather, name) * scale)
        info = np.iinfo(dtype)
        if scaled.min() < info.min or scaled.max() > info.max:
            raise ValueError(f"{name} does not fit the pack's storage range")
        arrays[name] = scaled.astype(dtype)
    full_meta = dict(meta)
    full_meta["pack_version"] = PACK_VERSION
    for name in _SCALARS:
        full_meta[name] = getattr(weather, name)
    np.savez_compressed(file, meta=np.array(json.dumps(full_meta)), **arrays)


def load_meta(file: Any) -> dict[str, Any]:
    """Read only the metadata of a weather pack."""
    with np.load(file) as pack:
        return json.loads(str(pack["meta"]))


def load_weather(file: Any) -> Weather:
    """Read a weather pack. `file` is a path or a binary file object."""
    with np.load(file) as pack:
        meta = json.loads(str(pack["meta"]))
        if meta.get("pack_version") != PACK_VERSION:
            raise ValueError("unsupported weather pack version")
        arrays = {name: pack[name].astype(float) / scale for name, (_, scale) in _FIELDS.items()}
        month = pack["month"]
    return Weather(month=month, **arrays, **{name: meta[name] for name in _SCALARS})
