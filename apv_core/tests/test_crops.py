import numpy as np
import pytest

from apv_core.constants import Season
from apv_core.crops import (
    CropParams,
    EvidenceGrade,
    is_selectable_by_default,
    needs_evidence_notice,
    relative_yield,
    season_light,
)
from apv_core.ranges import Case, Range


def test_relative_yield_hockey_stick():
    assert relative_yield(0.8, l_t=0.7, k=1.0) == pytest.approx(1.0)
    assert relative_yield(0.5, l_t=0.7, k=1.0) == pytest.approx(0.8)
    assert relative_yield(0.0, l_t=0.7, k=1.0) == pytest.approx(0.3)
    assert relative_yield(0.1, l_t=0.7, k=2.0) == pytest.approx(0.0)  # clipped at 0


def test_relative_yield_vectorised():
    out = relative_yield(np.array([1.0, 0.7, 0.6]), l_t=0.7, k=1.0)
    np.testing.assert_allclose(out, [1.0, 1.0, 0.9])


def test_season_light_means_season_months():
    monthly = np.arange(1, 13) / 12.0  # Jan=1/12 ... Dec=12/12
    assert season_light(monthly, Season.KHARIF) == pytest.approx(np.mean([6, 7, 8, 9, 10]) / 12)
    assert season_light(monthly, Season.RABI) == pytest.approx(np.mean([11, 12, 1, 2, 3]) / 12)
    grid = np.tile(monthly, (11, 1))
    assert season_light(grid, Season.ZAID).shape == (11,)


def _crop(**kw):
    base = {
        "id": "wheat",
        "name": "Wheat",
        "seasons": frozenset({Season.RABI}),
        "tolerance": "sensitive",
        "l_t": Range(0.9, 0.85, 0.8),
        "k": Range(1.2, 1.0, 0.8),
        "grade": EvidenceGrade.B,
    }
    base.update(kw)
    return CropParams(**base)


def test_crop_params_reject_inverted_case_order():
    with pytest.raises(ValueError):
        _crop(l_t=Range(0.8, 0.85, 0.9))


def test_crop_params_reject_bad_values():
    with pytest.raises(ValueError):
        _crop(k=Range(-0.1, -0.2, -0.3))
    with pytest.raises(ValueError):
        _crop(tolerance="hardy")


def test_evidence_rules():
    assert is_selectable_by_default(_crop(grade=EvidenceGrade.C))
    assert not is_selectable_by_default(_crop(grade=EvidenceGrade.D))
    assert needs_evidence_notice(_crop(grade=EvidenceGrade.C))
    assert not needs_evidence_notice(_crop(grade=EvidenceGrade.A))
    assert needs_evidence_notice(_crop(grade=EvidenceGrade.A, user_entered=True))


def test_range_get():
    r = Range(1.0, 2.0, 3.0)
    assert r.get(Case.CENTRAL) == 2.0 and r.get(Case.OPTIMISTIC) == 3.0
