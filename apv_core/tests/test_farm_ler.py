import numpy as np
import pytest
from fixtures import onion_rabi, soybean_kharif

from apv_core.constants import Season
from apv_core.farm import CropEconomics, SeasonCrop, baseline_income, revenue_weights, season_farm_income
from apv_core.ler import economic_ratio, energy_term, ler


def test_baseline_and_season_income():
    e = CropEconomics(yield_q_per_acre=10.0, price_per_q=4000.0, cost_per_acre=22000.0)
    assert baseline_income(e) == 18000.0
    out = season_farm_income(e, y_rel=np.array([1.0, 0.8]), a_farm=np.array([1.0, 0.95]), apv_cost_premium=0.05)
    np.testing.assert_allclose(
        out, [10 * 4000 * 1.0 * 1.0 - 22000 * 1.0 * 1.05, 10 * 4000 * 0.8 * 0.95 - 22000 * 0.95 * 1.05]
    )


def test_revenue_weights_sum_to_one():
    w = revenue_weights([soybean_kharif(), onion_rabi()])
    assert sum(w.values()) == pytest.approx(1.0)
    assert set(w) == {Season.KHARIF, Season.RABI}


def test_single_season_rotation_weights():
    assert revenue_weights([soybean_kharif()]) == {Season.KHARIF: 1.0}


def test_revenue_weights_zero_total_raises():
    sc = soybean_kharif()
    zero = SeasonCrop(sc.season, sc.crop, CropEconomics(0.0, 0.0, 1000.0))
    with pytest.raises(ValueError):
        revenue_weights([zero])


def test_revenue_weights_duplicate_season_raises():
    with pytest.raises(ValueError):
        revenue_weights([soybean_kharif(), soybean_kharif()])


def test_season_must_match_crop():
    sc = soybean_kharif()
    with pytest.raises(ValueError):
        SeasonCrop(Season.RABI, sc.crop, sc.economics)


def test_crop_economics_rejects_negative():
    with pytest.raises(ValueError):
        CropEconomics(-1.0, 4000.0, 1000.0)


def test_ler_and_energy_term():
    et = energy_term(np.array([0.0, 100.0]), np.array([0.0, 1500.0]), ref_energy_kwh_per_acre=300000.0)
    np.testing.assert_allclose(et, [0.0, 0.5])
    out = ler(
        {Season.KHARIF: 0.25, Season.RABI: 0.75},
        {Season.KHARIF: np.array([1.0, 0.8]), Season.RABI: np.array([1.0, 0.9])},
        et,
    )
    np.testing.assert_allclose(out, [1.0, 0.25 * 0.8 + 0.75 * 0.9 + 0.5])


def test_economic_ratio_none_when_baseline_nonpositive():
    assert economic_ratio(40000.0, 300000.0, 60000.0) == pytest.approx(340000.0 / 60000.0)
    assert economic_ratio(40000.0, 300000.0, 0.0) is None
    assert economic_ratio(40000.0, 300000.0, -5000.0) is None
