"""Single-axis tracker angle with backtracking, for a horizontal north-south axis (design spec §5.3)."""

import numpy as np


def tracker_rotation(zenith, azimuth, gcr: float, max_angle_deg: float) -> np.ndarray:
    """Signed panel rotation in degrees for each hour: positive faces west, negative faces east.

    The panels follow the sun (true tracking), turn back towards flat when a row would shade its neighbour
    (backtracking), and never turn past `max_angle_deg`. Zero when the sun is below the horizon.
    """
    zen = np.radians(np.asarray(zenith, dtype=float))
    az = np.radians(np.asarray(azimuth, dtype=float))
    true = np.arctan2(np.sin(zen) * np.sin(az - np.pi), np.cos(zen))
    t = np.abs(np.cos(true)) / gcr
    back = np.arccos(np.clip(t, -1.0, 1.0))  # zero where t >= 1: no neighbour shade to avoid
    theta = np.degrees(true - np.sign(true) * back)
    theta = np.clip(theta, -max_angle_deg, max_angle_deg)
    return np.where(np.asarray(zenith, dtype=float) >= 90.0, 0.0, theta)
