# D00: District list, LGD codes, boundaries, old-to-new district mapping, alias table

Full requirements: [`DATA_REQUIREMENTS.md` (D00)](../DATA_REQUIREMENTS.md).

**Put here:**
- lgd_districts.csv (state, state_lgd, district, district_lgd, alt_names)
- district_changes.csv (new_lgd, parent_lgd, change_type, date)
- boundaries (GeoPackage/Shapefile, EPSG:4326) plus a national outline that complies with Survey of India's boundary depiction
- district_aliases.csv (alias, district_lgd)

**Before processing anything:** copy `research/_templates/SOURCE.md` here (one per source) and fill it in.

`raw/` is git-ignored: paste large downloads there. Small CSVs, notes and `SOURCE.md` are committed.
