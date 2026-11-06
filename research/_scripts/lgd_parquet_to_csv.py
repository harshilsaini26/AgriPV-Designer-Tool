"""Convert LGD parquet snapshots (ramSeraph/opendata mirror of lgdirectory.gov.in) to committed CSVs.

Usage: uv run --no-project --with pandas --with pyarrow python -I lgd_parquet_to_csv.py <research_dir>
Reads  00_admin_boundaries/raw/lgd/{states,districts}.parquet
Writes 00_admin_boundaries/lgd_states.csv, 00_admin_boundaries/lgd_districts.csv
"""

import sys
from pathlib import Path

import pandas as pd


def main(research: Path) -> None:
    base = research / "00_admin_boundaries"
    raw = base / "raw" / "lgd"

    s = pd.read_parquet(raw / "states.parquet")
    s = s.rename(columns={"state_code": "state_lgd", "state_name": "state"})
    s["state_lgd"] = s["state_lgd"].astype(int)
    s = s.sort_values("state_lgd")
    s[
        ["state_lgd", "state", "state_or_ut", "state_census_2011_code", "state_census_2001_code", "state_version"]
    ].to_csv(base / "lgd_states.csv", index=False)

    d = pd.read_parquet(raw / "districts.parquet")
    d = d.rename(
        columns={
            "district_code": "district_lgd",
            "district_name": "district",
            "state_code": "state_lgd",
            "state_name": "state",
        }
    )
    for c in ("district_lgd", "state_lgd"):
        d[c] = d[c].astype(int)
    d["alt_names"] = ""  # filled later by the alias table (D00)
    d = d.sort_values(["state_lgd", "district_lgd"])
    cols = ["state", "state_lgd", "district", "district_lgd", "alt_names"]
    cols += ["district_census_2011_code", "district_census_2001_code"]
    d[cols].to_csv(base / "lgd_districts.csv", index=False)
    print(len(s), "states;", len(d), "districts")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
