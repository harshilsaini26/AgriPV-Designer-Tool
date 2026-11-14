# SOURCE: State regulator (SERC) orders on PM-KUSUM Component A tariffs

| Field | Value |
|---|---|
| Dataset ID | D19 |
| Publisher / owner | State Electricity Regulatory Commissions. Read in the orders: MPERC (Madhya Pradesh), OERC (Odisha), TGERC (Telangana), MERC (Maharashtra), GERC (Gujarat), JSERC (Jharkhand), KSERC (Kerala). From press or tender documents: RERC (Rajasthan), HERC (Haryana), UPERC (Uttar Pradesh), PSERC (Punjab) |
| Dataset name and version | Tariff orders for decentralised 0.5–2 MW solar plants under PM-KUSUM Component A, 2020–2026 (see the `regulator_order` and `order_date` columns) |
| URL / access route | One URL per state in `kusum_a_state_tariffs.csv` (`source_url`) |
| Accessed on (YYYY-MM-DD) | 2026-11-14 |
| Reference year(s) covered | Orders dated 2020-10-09 to 2025-12-20, plus a reported Haryana approval in 2026 |
| Spatial coverage | 11 states with a tariff; all others take the national fallback |
| Spatial unit or resolution | State |
| Temporal resolution | One-off orders, revised every few years |
| Licence | Public regulatory orders of Indian state commissions; no licence stated. Tariffs and parameters are public facts, extracted with citation |
| OK for a public open-source app? | OK (facts with citation; the order PDFs stay local in `raw/tariff_orders/`) |
| Required attribution text | "KUSUM-A tariff: [Commission], [order number], [date]" (per state, from the CSV) |
| Citation | e.g. Madhya Pradesh Electricity Regulatory Commission (2024). Order in Petition No. 13 of 2024: determination of pre-fixed levelised tariff for solar PV projects under Component A of PM-KUSUM, 20 June 2024 |
| Files in this folder | Committed: `kusum_a_state_tariffs.csv`. Git-ignored: `raw/tariff_orders/` (MPERC 2024, OERC 2024 and 2025 ×2, TGERC 2025, MERC 2023, GERC 2025, JSERC 2020 and KSERC 2021 order PDFs; press pages) |
| Units and key column meanings | `tariff_inr_per_kwh` (₹/kWh, levelised over the 25-year PPA unless stated); `tariff_type` (pre-fixed levelised ceiling, auction-discovered or generic); `status`: `verified` = read in the regulator's own order, `unverified` = press or tender only, `needs_update` = a newer order exists but its figure was not found, `fallback` = national default |
| Known caveats and gaps | (1) **No Component A tariff was found for Karnataka, Tamil Nadu, Chhattisgarh, Bihar, Andhra Pradesh, West Bengal, Himachal Pradesh or Uttarakhand.** They use the national fallback (₹3.11, the median of the eleven states) with a `state_fallback` flag, as spec assumption A-4 allows. Component A activity is concentrated in a few states: by June 2026 Rajasthan had 1,236 of the 1,727 MW installed nationally (Lok Sabha answer of 29 July 2026, as reported). Sanctions at end-2025 were led by Rajasthan (5,618 MW), Telangana (1,797 MW) and Madhya Pradesh (1,401 MW). (2) Most tariffs are ceilings, and auctions can clear lower. Odisha shows the opposite pattern: ₹3.08 drew no projects, so it rose to ₹4.40 and then settled at ₹3.76 in a fresh auction. (3) **Rajasthan revised its tariff in Nov 2025**, and the new figure was not found; the RERC order is needed. (4) Haryana, Uttar Pradesh and Punjab come from press or tender documents. The UP figure is an old ceiling, and its recent ₹2.48–2.99 approvals are for Component C-2, not A. (5) Older orders (Punjab 2020, Jharkhand and Kerala 2021) predate module price changes, customs duty and ALMM rules |
| Processing notes | Values were read from the order PDFs (PyMuPDF text extraction). The MPERC order also supplies capital cost, O&M, financing and lease parameters, used in `../capex_om/` and `../land_lease/`. The MNRE PM-KUSUM dashboard (pmkusum.mnre.gov.in) did not load state-wise figures when checked |
