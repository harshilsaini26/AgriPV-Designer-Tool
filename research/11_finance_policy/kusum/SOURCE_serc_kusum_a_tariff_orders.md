# SOURCE: State regulator (SERC) orders on PM-KUSUM Component A tariffs

| Field | Value |
|---|---|
| Dataset ID | D19 |
| Publisher / owner | State Electricity Regulatory Commissions: MPERC (Madhya Pradesh), OERC (Odisha), TGERC (Telangana), JSERC (Jharkhand), KSERC (Kerala); plus press reports of RERC (Rajasthan), GERC (Gujarat), HERC (Haryana) and PSERC (Punjab) decisions |
| Dataset name and version | Tariff orders for decentralised 0.5–2 MW solar plants under PM-KUSUM Component A, 2021–2025 (see the `regulator_order` and `order_date` columns) |
| URL / access route | One URL per state in `kusum_a_state_tariffs.csv` (`source_url`) |
| Accessed on (YYYY-MM-DD) | 2026-11-14 |
| Reference year(s) covered | Orders dated 2021-01-08 to 2025-04-22 |
| Spatial coverage | 9 states with a tariff; all others take the national fallback |
| Spatial unit or resolution | State |
| Temporal resolution | One-off orders, revised every few years |
| Licence | Public regulatory orders of Indian state commissions; no licence stated. Tariffs and parameters are public facts, extracted with citation |
| OK for a public open-source app? | OK (facts with citation; the order PDFs stay local in `raw/tariff_orders/`) |
| Required attribution text | "KUSUM-A tariff: [Commission], [order number], [date]" (per state, from the CSV) |
| Citation | e.g. Madhya Pradesh Electricity Regulatory Commission (2024). Order in Petition No. 13 of 2024: determination of pre-fixed levelised tariff for solar PV projects under Component A of PM-KUSUM, 20 June 2024 |
| Files in this folder | Committed: `kusum_a_state_tariffs.csv`. Git-ignored: `raw/tariff_orders/` (MPERC 2024, OERC 2024, TGERC 2025, JSERC 2020 and KSERC 2021 order PDFs; a press page for the Rajasthan revision) |
| Units and key column meanings | `tariff_inr_per_kwh` (₹/kWh, levelised over the 25-year PPA unless stated); `tariff_type` (pre-fixed levelised ceiling, auction-discovered or generic); `status`: `verified` = read in the regulator's own order, `unverified` = press or tender only, `needs_update` = a newer order exists but its figure was not found, `fallback` = national default |
| Known caveats and gaps | (1) **No tariff found for Maharashtra, Uttar Pradesh, Karnataka, Tamil Nadu, Chhattisgarh, Bihar, Andhra Pradesh or West Bengal.** They use the national fallback (₹3.11, the median of the nine states) with a `state_fallback` flag, as spec assumption A-4 allows. Maharashtra's farm-solar programme runs mostly through its own MSKVY scheme. (2) Most tariffs are ceilings: auctions can clear lower. Odisha went the other way, raising its tariff to ₹4.40 after no plant was built at ₹3.08. (3) Rajasthan revised its tariff in Nov 2025, and the new figure was not found. (4) Gujarat, Haryana and Punjab are from press or tender documents, not the orders themselves. (5) Older orders (Jharkhand 2021, Kerala 2021) predate module price changes, customs duty and ALMM rules, and may be out of date |
| Processing notes | Values were read from the order PDFs (PyMuPDF text extraction). The MPERC order also supplies capital cost, O&M, financing and lease parameters, used in `../capex_om/` and `../land_lease/` |
