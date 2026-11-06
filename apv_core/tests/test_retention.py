import numpy as np
import pytest

from apv_core.constants import GCR_GRID, Season
from apv_core.retention import allowed_gcr, outside_limit, retention

K = np.array([1.0, 1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55])
R = np.array([1.0, 0.99, 0.97, 0.94, 0.9, 0.86, 0.82, 0.78, 0.74, 0.7, 0.66])


def test_retention_is_a_farm_times_yield():
    np.testing.assert_allclose(retention(0.95, np.array([1.0, 0.8])), [0.95, 0.76])


def test_allowed_gcr_uses_strictest_season():
    assert allowed_gcr(GCR_GRID, {Season.KHARIF: K, Season.RABI: R}, 0.80) == 0.25


def test_allowed_gcr_exact_limit_passes():
    assert allowed_gcr(GCR_GRID, {Season.KHARIF: K}, 0.80) == 0.25  # K[5] == 0.80 exactly


def test_allowed_gcr_float_noise_at_limit_passes():
    noisy = K.copy()
    noisy[5] = 0.8 - 1e-12
    assert allowed_gcr(GCR_GRID, {Season.KHARIF: noisy}, 0.80) == 0.25


def test_allowed_gcr_none_when_first_step_fails():
    low = np.array([1.0] + [0.5] * 10)
    assert allowed_gcr(GCR_GRID, {Season.RABI: low}, 0.80) is None


def test_allowed_gcr_stops_at_first_failure_even_if_later_recovers():
    bumpy = np.array([1.0, 0.9, 0.7, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9])
    assert allowed_gcr(GCR_GRID, {Season.KHARIF: bumpy}, 0.80) == 0.05


def test_outside_limit_flags():
    flags = outside_limit({Season.KHARIF: K, Season.RABI: R}, 0.80)
    assert flags.tolist() == [False] * 6 + [True] * 5


def test_limit_validation():
    with pytest.raises(ValueError):
        allowed_gcr(GCR_GRID, {Season.KHARIF: K}, 0.4)
    with pytest.raises(ValueError):
        allowed_gcr(GCR_GRID, {}, 0.8)
