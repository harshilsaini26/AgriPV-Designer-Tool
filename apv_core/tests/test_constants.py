from apv_core.constants import ACRE_M2, DEFAULT_POLICY_LIMIT, GCR_GRID, SEASON_MONTHS, Season


def test_gcr_grid_is_eleven_steps_from_zero_to_half():
    assert len(GCR_GRID) == 11
    assert GCR_GRID[0] == 0.0 and GCR_GRID[-1] == 0.5
    assert GCR_GRID[3] == 0.15  # exact after rounding, no float noise


def test_season_months():
    assert SEASON_MONTHS[Season.KHARIF] == (6, 7, 8, 9, 10)
    assert SEASON_MONTHS[Season.RABI] == (11, 12, 1, 2, 3)
    assert SEASON_MONTHS[Season.ZAID] == (3, 4, 5, 6)


def test_units_and_defaults():
    assert ACRE_M2 == 4046.86
    assert DEFAULT_POLICY_LIMIT == 0.80
