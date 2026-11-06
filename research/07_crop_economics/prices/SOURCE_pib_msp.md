# SOURCE: Minimum Support Prices (MSP): PIB releases for Kharif 2026-27 and Rabi 2027-28

| Field | Value |
|---|---|
| Dataset ID | D13 |
| Publisher / owner | Press Information Bureau (PIB), for the Cabinet Committee on Economic Affairs / Ministry of Agriculture & Farmers Welfare (MSPs recommended by CACP) |
| Dataset name and version | (1) "Cabinet approves Minimum Support Prices (MSP) for Kharif Crops for Marketing Season 2026-27", PIB Delhi, 13 May 2026, Release ID 2260618. (2) "Cabinet approves Minimum Support Prices (MSP) for Rabi Crops for Marketing Season 2027-28", PIB Delhi, 30 Sep 2026, Release ID 2316941 |
| URL / access route | https://www.pib.gov.in/PressReleasePage.aspx?PRID=2260618 and https://www.pib.gov.in/PressReleasepage.aspx?PRID=2316941 (tables read from the release pages) |
| Accessed on (YYYY-MM-DD) | 2026-11-06 |
| Reference year(s) covered | KMS 2026-27 (with 2025-26 and 2013-14 for comparison); RMS 2027-28 (with 2026-27) |
| Spatial coverage | All-India (single national price) |
| Spatial unit or resolution | National |
| Temporal resolution | Per marketing season |
| Licence | Government press releases, free to reproduce with attribution |
| OK for a public open-source app? | OK with attribution |
| Required attribution text | "MSP: Government of India (CCEA / PIB release IDs 2260618, 2316941)" |
| Citation | PIB (2026). Release IDs 2260618 (13 May 2026) and 2316941 (30 Sep 2026) |
| Files in this folder | Committed: `msp_kharif2026-27_rabi2027-28.csv` (23 rows) |
| Units and key column meanings | ₹ per quintal. `cost_a2fl_inr_per_qtl` = all-India weighted average cost of production (A2+FL) used by CACP; `margin_over_cost_pct`; `msp_previous_season_inr_per_qtl`; `msp_2013_14_inr_per_qtl` (kharif only); `source_prid` |
| Known caveats and gaps | (1) MSP is a **floor price, not the realised farm-gate price**: many crops sell below MSP outside procurement states, so use MSP as an upper-central case and mandi modal prices (Agmarknet / UPAg) or Farm Harvest Prices (DES FHP) for realised prices. (2) No MSP for vegetables and fruit (onion, potato, tomato), so their prices must come from Agmarknet / NHRDF. (3) Copra, jute and sugarcane (FRP) MSPs are announced separately and are not included yet |
| Processing notes | Transcribed from the release HTML tables (values checked against the release text) |
