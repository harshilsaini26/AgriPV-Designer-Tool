# SOURCE: Local Government Directory (LGD): states, districts, sub-districts (snapshot 2026-11-01)

| Field | Value |
|---|---|
| Dataset ID | D00 |
| Publisher / owner | Ministry of Panchayati Raj, Government of India: Local Government Directory (https://lgdirectory.gov.in). Mirror: `ramSeraph/opendata` (GitHub Pages), which scrapes the official LGD reports daily and republishes them as Parquet with SHA-256 checksums |
| Dataset name and version | LGD daily snapshot `observed_on` **2026-11-01**: `states` (36 rows), `districts` (790 rows), `subdistricts` (7,099 rows). File hashes: districts `8edd1bf95e5bfeec…`, states `3a760944dab3b3ff…`, subdistricts `6ec72ad8061cea3d…` |
| URL / access route | Index: https://ramseraph.github.io/opendata/lgd/data/metadata.json, which lists each dataset's Parquet URL. Official equivalent: https://lgdirectory.gov.in/downloadDirectory.do ("All Districts of India", XLS/PDF; per the mirror's README, the official CSV export no longer works) |
| Accessed on (YYYY-MM-DD) | 2026-11-06 |
| Reference year(s) covered | Administrative units in force on 2026-11-01 |
| Spatial coverage | All-India |
| Spatial unit or resolution | State, district, sub-district (codes only, no geometry) |
| Temporal resolution | Daily snapshot (the mirror also keeps a cumulative `changes` report: 1.5 M rows, not downloaded) |
| Licence | Official LGD data is Government of India public data. LGD extracts on data.gov.in are published under the Government Open Data Licence – India (GODL). The mirror repo asserts no licence ("NOASSERTION") but redistributes the official records unchanged |
| OK for a public open-source app? | OK with attribution (GODL-equivalent public directory). The code lists are committed |
| Required attribution text | "Administrative codes: Local Government Directory, Ministry of Panchayati Raj, Government of India (lgdirectory.gov.in)" |
| Citation | Ministry of Panchayati Raj (2026). Local Government Directory, district and state lists as on 01-11-2026. Retrieved via ramSeraph/opendata LGD mirror |
| Files in this folder | Committed: `lgd_states.csv` (36), `lgd_districts.csv` (790). Git-ignored: `raw/lgd/{states,districts,subdistricts}.parquet`, `raw/lgd/metadata.json`, `raw/lgd/districts_manifest.json` |
| Units and key column meanings | `lgd_districts.csv`: `state`, `state_lgd`, `district`, `district_lgd` (**the join key for the whole project**), `alt_names` (empty; to be filled by the alias table), `district_census_2011_code`, `district_census_2001_code`. `lgd_states.csv`: `state_lgd`, `state`, `state_or_ut` (S/U), Census codes, `state_version` |
| Known caveats and gaps | (1) 790 LGD districts vs 820 boundary polygons (datta07, which includes disputed slivers and older or newer splits) vs 715–757 districts in crop and groundwater statistics: building the **alias / crosswalk table** is the next D00 task. (2) Census 2011 codes are blank for districts created after 2011. (3) The mirror is a third party; for anything legal, re-download from lgdirectory.gov.in |
| Processing notes | `research/_scripts/lgd_parquet_to_csv.py` (pandas + pyarrow) |
