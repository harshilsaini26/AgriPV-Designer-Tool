import pytest
from fixtures import elevated_structure, finance_defaults, onion_rabi, soybean_kharif, synthetic_physics

from apv_core import GCR_GRID, BusinessModel, Case, NoticeCode, Season, SweepInputs, run_sweep


def inputs(**kw):
    base = {
        "physics": synthetic_physics(),
        "structure": elevated_structure(),
        "rotation": (soybean_kharif(), onion_rabi()),
        "finance": finance_defaults(),
        "business_model": BusinessModel.KUSUM_A,
    }
    base.update(kw)
    return SweepInputs(**base)


def test_sweep_shape():
    r = run_sweep(inputs())
    assert r.gcr == GCR_GRID
    assert all(len(r.metrics[k]) == 11 for k in r.metrics)
    assert set(r.retention) == {Season.KHARIF, Season.RABI}


def test_gcr_zero_is_exact_baseline():
    r = run_sweep(inputs())
    for case in Case:
        assert r.metrics["ler"][0].get(case) == pytest.approx(1.0)
        assert r.metrics["farm_income"][0].get(case) == pytest.approx(r.baseline_farm_income)
        assert r.metrics["kwp_per_acre"][0].get(case) == 0.0
        assert r.metrics["project_irr"][0].get(case) is None
        assert r.metrics["payback_years"][0].get(case) is None


def test_case_ordering_for_farm_income():
    r = run_sweep(inputs())
    for rng in r.metrics["farm_income"]:
        assert rng.pessimistic <= rng.central + 1e-6 <= rng.optimistic + 2e-6


def test_allowed_gcr_and_policy_flags_agree():
    r = run_sweep(inputs())
    a = r.allowed_gcr.central
    assert a is not None
    idx = GCR_GRID.index(a)
    assert not any(r.outside_policy[: idx + 1])


def test_no_allowed_gcr_notice_with_strict_limit():
    r = run_sweep(inputs(policy_limit=1.0))
    assert r.allowed_gcr.central is None
    assert any(n.code is NoticeCode.NO_ALLOWED_GCR for n in r.notices)


def test_outside_policy_notice():
    r = run_sweep(inputs())
    assert any(n.code is NoticeCode.OUTSIDE_POLICY_LIMIT for n in r.notices)


def test_low_evidence_notice_for_grade_c_crop():
    r = run_sweep(inputs())  # onion fixture is grade C
    assert any(n.code is NoticeCode.LOW_EVIDENCE_CROP for n in r.notices)


def test_kusum_size_notice():
    r = run_sweep(inputs(land_acres=20.0))  # >2 MW at high GCR
    assert any(n.code is NoticeCode.KUSUM_SIZE_OUT_OF_RANGE for n in r.notices)


def test_lease_metrics_only_for_lease():
    k = run_sweep(inputs())
    assert all(rg.central is None for rg in k.metrics["max_affordable_lease"])
    lease = run_sweep(inputs(business_model=BusinessModel.LEASE))
    assert lease.metrics["max_affordable_lease"][6].central is not None


def test_sweep_kharif_only():
    r = run_sweep(inputs(rotation=(soybean_kharif(),)))
    assert set(r.retention) == {Season.KHARIF}
    assert r.metrics["ler"][0].central == pytest.approx(1.0)


def test_per_season_ler_derivable_from_energy_term():
    r = run_sweep(inputs())
    i = 6
    season_ler = r.retention[Season.RABI][i].central + r.metrics["energy_term"][i].central
    assert season_ler > r.retention[Season.RABI][i].central


def test_inputs_validation():
    with pytest.raises(ValueError):
        inputs(policy_limit=0.3)
    with pytest.raises(ValueError):
        inputs(rotation=(soybean_kharif(), soybean_kharif()))
