# SOURCE: LGD district boundaries with LGD codes (Bharatlas `lgd_districts`, via yashveeeeeeer/india-geodata)

| Field | Value |
|---|---|
| Dataset ID | D00 |
| Publisher / owner | Codes: Local Government Directory (Government of India). Polygons compiled by `yashveeeeeeer/india-geodata` (repo licence CC BY 4.0; its admin boundaries come from `ramSeraph/indian_admin_boundaries`, CC0 1.0). Served by Bharatlas (urbanmorph/geodata) |
| Dataset name and version | Bharatlas layer `lgd_districts`, 785 polygons ("Districts (2024)"); fields include `year_stat` (e.g. `2011_c`) |
| URL / access route | `https://bharatlas.com/api/v1/layers/lgd_districts`, file `https://pub-0429b8e3b5a946e69ea007df844a6f1c.r2.dev/admin/districts/LGD_Districts.parquet` (22.2 MB). Also as GeoJSON (93 MB) and Shapefile (39 MB) |
| Accessed on (YYYY-MM-DD) | 2026-11-06 |
| Reference year(s) covered | LGD snapshot of about 2024 |
| Spatial coverage | All-India (36 states/UTs) |
| Spatial unit or resolution | District polygons with LGD codes |
| Temporal resolution | Snapshot |
| Licence | "CC0-1.0 / CC-BY-4.0" (Bharatlas API); CC BY 4.0 per the india-geodata README |
| OK for a public open-source app? | OK with attribution (treat it as CC BY 4.0, the stricter of the two). The national outline still needs checking against Survey of India's depiction before publishing a map |
| Required attribution text | "District boundaries: Local Government Directory codes; geometry from india-geodata (CC BY 4.0) / ramSeraph indian_admin_boundaries (CC0), via Bharatlas" |
| Citation | yashveeeeeeer (2026). india-geodata: LGD district boundaries. GitHub. Via Bharatlas, https://bharatlas.com/view/lgd_districts |
| Files in this folder | Git-ignored: `raw/bharatlas/LGD_Districts.parquet`. Used to build `01_agro_climate/zones/district_zone_*.csv` |
| Units and key column meanings | `dist_lgd` (LGD district code, the project join key), `dtname`, `state_lgd`, `stname`, `stcode11` / `dtcode11` (Census 2011), `year_stat`, `remarks`, `SHAPE_Area` (m², source projection). CRS: EPSG:4326 |
| Known caveats and gaps | **Compared with the LGD directory snapshot of 2026-11-01 (`lgd_districts.csv`, 790 rows):** (1) 19 districts created in 2024–26 have **no polygon**: LGD 784–802, i.e. Maihar and Pandhurna (MP); Keyi Panyor and Bichom (Arunachal); Meluri (Nagaland); Vav-Tharad (Gujarat); Markapuram and Polavaram (AP); Hansi (Haryana); Kushavati (Goa); Outer North, Old Delhi and Central North (Delhi); Sham, Changthang, Nubra, Zanskar, Drass and Sankoo (Ladakh). These must inherit attributes from their parent districts. (2) 13 polygons are **not in the current LGD list**: Mirpur (code 0, PoK), Mahe (599), Yanam (601), Shahdara (671), and the Rajasthan districts abolished in Dec 2024 (Dudu 769, Gangapur City 771, Neem Ka Thana 773, Anoopgarh 776, Jodhpur Gramin 778, Sanchor 779, Shahpura 780, Kekri 781, Jaipur Gramin 783). Mahe and Yanam may have been recoded; check them. (3) This replaces the datta07 layer (no LGD codes) as the primary boundary layer; datta07 stays for the centroid points already used by the NASA POWER and Global Solar Atlas tables |
| Processing notes | Comparison done ad hoc against `lgd_districts.csv`. Next: a `district_lineage.csv` (child LGD → parent LGD → share) to fill the 19 new districts and to remap the abolished ones |
