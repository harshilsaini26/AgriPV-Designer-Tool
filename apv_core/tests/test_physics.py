import pytest
from fixtures import elevated_structure, synthetic_physics

from apv_core.physics import PhysicsTable, Structure, farmable_fraction, kwp_per_acre


def test_kwp_per_acre():
    assert kwp_per_acre(0.30, 0.215) == pytest.approx(0.30 * 4046.86 * 0.215)  # ≈ 261.0
    assert kwp_per_acre(0.0, 0.215) == 0.0


def test_farmable_fraction_is_one_at_gcr_zero():
    s = elevated_structure()
    assert farmable_fraction(0.0, s) == 1.0
    assert farmable_fraction(0.25, s) == 0.95


def test_physics_table_validates_shape_and_baseline_row():
    p = synthetic_physics()
    bad_light = p.light_fraction.copy()
    bad_light[0, 0] = 0.9
    with pytest.raises(ValueError):
        PhysicsTable(p.energy_kwh_per_kwp, bad_light, p.ref_energy_kwh_per_acre)
    with pytest.raises(ValueError):
        PhysicsTable(p.energy_kwh_per_kwp[:10], p.light_fraction, p.ref_energy_kwh_per_acre)


def test_physics_table_is_read_only():
    p = synthetic_physics()
    with pytest.raises(ValueError):
        p.light_fraction[1, 1] = 0.0


def test_structure_validation():
    with pytest.raises(ValueError):
        Structure("x", a_farm=1.2, module_efficiency=0.2)
