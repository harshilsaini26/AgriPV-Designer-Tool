# PM-KUSUM Component A: rules extracted for apv_core

Source: MNRE, *Comprehensive guidelines of PM-KUSUM*, 17 Jan 2024 (`SOURCE_mnre_pm_kusum.md`). Section numbers
refer to that document. Check the later OMs (2026-04-26, 2026-09-28) before treating any value as current.

| Rule | Value | Section | Used in model as |
|---|---|---|---|
| Scope | 10,000 MW of decentralised **ground- or stilt-mounted** grid-connected solar / other RE plants by farmers on their land | 2.1(i), 4.1(i) | Eligibility: stilt-mounted = agrivoltaic structures qualify |
| Plant size | **500 kW to 2 MW** per plant (Renewable Power Generator, RPG) | 4.1(ii) | `KUSUM_A_MIN_MW` = 0.5, `KUSUM_A_MAX_MW` = 2.0 (already in `apv_core.constants`) |
| Who can be the RPG | Individual farmers, groups of farmers, cooperatives, panchayats, FPOs, Water User Associations; directly or through a developer | 4.2 | Business model: KUSUM-A owner-operator vs developer / lease |
| Land lease route | If the land is given to a developer / DISCOM, the landowner gets lease rent "as mutually agreed", either **₹/acre/year or ₹/kWh generated per acre**; it can be paid directly by the DISCOM out of the developer's dues; model Land Lease Agreement in Annexure I | 4.2(ii) | Lease model: support both a fixed ₹/acre/yr and a ₹/kWh-linked lease |
| Location | Preferably within **5 km of a 33/11, 66/11 or 110/11 kV sub-station** | 4.1(iii), 4.3 | Advisory note (no sub-station data in the tool yet) |
| Capacity notification | DISCOM notifies substation-wise injectable capacity on its website | 4.3(i) | Not modelled |
| Tariff | DISCOM buys all power at a **pre-fixed levelised tariff** (set by the state). If oversubscribed, bidding is held with that tariff as the ceiling | 4.4(iii, v, vi) | `tariff_per_kwh` input; state defaults from SERC orders (to collect) |
| PPA | **25 years from COD**; DISCOM must buy all power within the contract capacity; extension beyond 25 years by mutual agreement; escrow as payment security | 4.6 | `ANALYSIS_YEARS` = 25 |
| Bank guarantees | EMD ₹1 lakh/MW (bidding route), converted to a Performance BG valid 15 months from LoA | 4.7 | Minor upfront cost (optional) |
| Connectivity | RPG builds the dedicated 11/33 kV line to the sub-station plus the bay and switchgear | 4.8 | CAPEX adder: grid line ₹/km (to collect, D20) |
| Incentive to DISCOM | PBI of **₹0.40/kWh or ₹6.6 lakh/MW/yr, whichever is lower, for 5 years** from COD (paid to the DISCOM, not the farmer) | 4.9, 4.12.1 | Not a farmer cash flow (context only) |
| CUF benchmark | Minimum annual CUF of **19%** used for capacity sizing (stated for feeder-level solarisation, Component C) | Comp C annexure | Sanity check on the energy model: AC CUF below about 17% should trigger a notice |
| RESCO commissioning | Up to 12 months from LoA (feeder-level solarisation) | Comp C | n/a |
