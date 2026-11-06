# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Vite + React + TypeScript frontend with MapLibre GL for the district map. Python FastAPI on the Vercel Python runtime for the API. An offline Python data pipeline (run locally or in GitHub Actions) builds versioned data artefacts. Hosted on Vercel (Hobby plan for now; Pro if used commercially). Code lives in one GitHub repo.

## Users

Professional intermediaries who assess agrivoltaic (APV) projects for or with farmers: FPOs, NGOs, EPC firms and consulting firms in India. They work desktop-first, usually at a desk preparing a proposal, feasibility note or board discussion. A typical session starts with a **district they already have in mind** (a client's or FPO's home district, a project location) rather than open-ended screening. The project is also an academic and portfolio piece, so methodology must hold up to scrutiny.

Farmers are not direct users. They are reached through these intermediaries and the reports they produce.

## Product Purpose

The app helps users understand whether and how agrivoltaics fits a given Indian district by combining district-level context (agro-climate, soil, elevation, groundwater and irrigation, major crops and crop economics, solar resource) with a design and techno-economic model. The core question it answers is: **as ground coverage ratio (GCR) and structure type change, how do farm income and energy income per acre trade off, and what is the land equivalent ratio (LER)?**

Success means the user leaves with a **client-ready report** (PDF, plus Excel cash flows) they can hand to a client, funder, bank or FPO board, with every number traceable to its source and method.

## Positioning

Existing tools are either US-centric techno-economic calculators (NREL's ADAM: US tax, MACRS, NSRDB, $/acre, no API) or shading/experiment designers with no finance or crop model. This product is built on Indian district data and Indian business models (PM-KUSUM Component A owner-operator, and land lease to a developer). It models crop response to shade by season (kharif, rabi, zaid), flags groundwater stress, and reports in ₹ per acre.

## Operating Context

- Unit of analysis is the **district** (~780, keyed by LGD codes). Finer resolution is out of scope because the data doesn't support it.
- Workflow: pick a district → review its context → choose business model (KUSUM-A or lease) → structure preset → crop rotation → finance inputs (pre-filled with state defaults) → GCR sweep → inspect the optimum → export a report.
- Physics (energy per kWp, ground light fraction) is pre-computed per district for preset structure configurations. Crop response and finance run live in the API.
- Outputs feed DPRs, proposals, bank and NABARD conversations, and FPO board decisions.

## Capabilities and Constraints

- Business models in v1: PM-KUSUM Component A (farmer/FPO owner, DISCOM tariff) and land lease (developer-owned; includes max affordable lease at a target IRR). KUSUM-C and C&I/open access are deferred.
- Metrics: farm income and energy income per acre, LER (with an explicit reference-PV assumption), economic ratio, project and equity IRR, NPV, payback, DSCR, LCOE, kWp per acre, plant size versus KUSUM limits.
- Yield-retention limit presets: DIN SPEC 91434 (≥ 66%) and the Japanese rule (≥ 80%); user-editable.
- Crop shade response uses cited low/central/high parameters shown as an uncertainty band. The heat-relief uplift is off by default.
- Every field carries source, year, method and licence. Districts carry data-quality flags (missing, state-level fallback, boundary-mapped).
- English first; strings kept in translation files for Hindi and regional languages later. No user accounts in v1.
- Out of scope: site-level geometry, substation distance, geotechnical conditions.

## Brand Commitments

No name or brand yet. Use a working placeholder name. The visual identity is open.

## Evidence on Hand

No real data artefacts, case studies, customers or testimonials exist yet. Demonstration data must be labelled synthetic until the pipeline produces real district data. Never invent client names, deployments or benchmark claims.

## Product Principles

1. **Traceable over impressive.** Every number shows where it came from, and uncertainty is shown, not hidden.
2. **The district is the unit.** Don't imply site-level precision the data can't support.
3. **The trade-off is the product.** The farm-versus-energy GCR curve and LER are the centre of every analysis.
4. **Built for the handoff.** The session ends in an artefact a third party will read without the app.
5. **Indian context first.** Indian schemes, units (₹, acres, kharif/rabi), data sources and constraints come first; global defaults never do.
