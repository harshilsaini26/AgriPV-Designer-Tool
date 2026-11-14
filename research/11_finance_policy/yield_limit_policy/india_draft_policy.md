# India's yield-retention limit: what exists (checked 2026-11-14)

**Short answer: no Indian body has published a yield-retention rule.** The 80% figure in the spec comes from
policymaker conversations. No public document sets it, and none defines how it would be measured.
The app keeps 80% as an editable draft line (REQ-POL-01).

## What has been published

| Date | Body | What it says | Measurement definition |
|---|---|---|---|
| 2024 | India Agrivoltaics Alliance (industry; NSEFI secretariat), *Guidebook for Policy Makers*, p. 28 | Proposes a cap on yield loss of **10–20%**, which would mean keeping **80–90%** of the yield. It also proposes restricting key staple food crops, at least 70% of land under cultivation, at most 30% under solar, a minimum height of 1.5–2 m and plant sizes of 100 kW–5 MW. The limit "can be refined" from pilot data | None given (no baseline, area basis or period) |
| Oct 2025 | Power Foundation of India (a society under the Ministry of Power) with CPI, *Tapping the Potential of Agriphotovoltaics in India*, pp. 11, 35 | Notes that the Ministry of Agriculture and Farmers Welfare "has not prescribed minimum agricultural yield thresholds". Recommends that it notify thresholds "in % of baseline yield" or cap the permissible loss, varying them by **crop type**, **region (rainfed vs irrigated)** and **season (kharif vs rabi)**. PM-KUSUM, VGF and farm-income benefits would depend on meeting them. Gives no number | % of a baseline yield, set per crop and season; the baseline is not defined |
| 19–28 Oct 2026 | MNRE (Secretary S. K. Sarangi; Minister Pralhad Joshi), at and after the Agrivoltaics World Conference 2026 | Announces a draft national agrivoltaics policy with an initial 5 GW over 3–4 years and a possible 10 GW agri-PV component in PM-KUSUM 2.0. The draft "would be released publicly" for comments from states and stakeholders. Reported tariffs are ₹3.20–3.30/kWh for elevated agrivoltaics. Germany's yield-linked support is "being examined". The Agriculture Minister said designs must preserve cultivation and allow machinery | None reported. **The draft was not found on 2026-11-14** |

## What this means for Q-01 to Q-03

- **Q-01 (the value).** Still open. The published proposals point to 80–90% retention: the Alliance's 10–20% loss cap and Japan's 80%, which is the most-cited precedent. Germany (66%) is looser, and France (90%) is stricter. Keep the default at 80%, editable from 50% to 100%.
- **Q-02 (area basis).** No Indian source defines it. Abroad, **France** measures yield per hectare of the agricultural parcel against an unshaded control zone. That parcel-wide measure is close to `a_farm × Y_rel` (per acre of land). **Japan** compares the unit yield of the farmland under the panels with the regional average for the same crop and year. Its posts are a separate land conversion, so Japan's measure is close to `Y_rel` (per cropped area). **Recommendation: keep the stricter per-acre-of-land default, and add a per-cropped-area option labelled with Japan's rule.**
- **Q-03 (season or year).** The PFI recommendation of separate thresholds for kharif and rabi supports checking each season. Japan also checks each crop every year. France uses a mean yield with no stated period. **Recommendation: keep the per-season default.**
- **When the MNRE draft appears**, re-check all three. A per-crop or regional baseline, such as the district average, would change the comparison from "same field without panels" to "district average yield". The app's open-field baseline is the same district and crop at GCR 0, which is closest to France's control zone.

Sources: `yield_limit_rules.csv` (one row per document with its URL), and `SOURCE_yield_limit_policy.md`.
