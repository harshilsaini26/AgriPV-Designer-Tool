import pytest

from apv_core.cashflow import annuity_payment, escalating_annuity_factor, irr, npv, simple_payback


def test_npv_reference():
    assert npv(0.10, [-100, 60, 60]) == pytest.approx(4.1322, abs=1e-4)


def test_irr_reference():
    r = irr([-100, 60, 60])
    assert r.value == pytest.approx(0.130662, abs=1e-6) and r.reason is None


def test_irr_undefined_without_sign_change():
    r = irr([0, 0, 0])
    assert r.value is None and "never change sign" in r.reason
    r = irr([-100, -10, -10])
    assert r.value is None


def test_payback_interpolated():
    assert simple_payback([-100, 30, 30, 30, 30]) == pytest.approx(10 / 3)
    assert simple_payback([-100, 10, 10]) is None
    assert simple_payback([0, 10, 10]) is None


def test_escalating_annuity_factor_reference():
    assert escalating_annuity_factor(0.10, 0.0, 2) == pytest.approx(1.735537, abs=1e-6)
    assert escalating_annuity_factor(0.10, 0.05, 2) == pytest.approx(1.776860, abs=1e-6)


def test_annuity_payment():
    assert annuity_payment(1000.0, 0.0, 4) == 250.0
    assert annuity_payment(1000.0, 0.10, 2) == pytest.approx(576.190, abs=1e-3)
