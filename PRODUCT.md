# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Vite + React + TypeScript frontend with MapLibre GL for the district map. Python FastAPI on the Vercel Python runtime for the API. An offline Python data pipeline (run locally or in GitHub Actions) builds versioned data artefacts. Hosted on Vercel (Hobby plan for now; Pro if used commercially). Code lives in one GitHub repo.

## Users

Professional intermediaries who assess agrivoltaic (APV) projects for or with farmers: FPOs, NGOs, EPC firms and consulting firms in India. They work desktop-first, usually at a desk preparing a proposal, feasibility note or board discussion. A typical session starts with a **district they already have in mind** (a client's or FPO's home district, a project location) rather than open-ended screening. The project is also an academic and portfolio piece, so methodology must hold up to scrutiny.

Farmers are not direct users. They are reached through these intermediaries and the estimates they share.

## Product Purpose

The app helps users understand whether and how agrivoltaics fits a given Indian district by combining district-level context (agro-climate, soil, elevation, groundwater and irrigation, major crops and crop economics, solar resource) with a design and techno-economic model. The core question it answers is: **as ground coverage ratio (GCR) and structure type change, how do farm income and energy income per acre trade off, and what is the land equivalent ratio (LER)?**

It is a **knowledge tool, not a report generator**: it gives rough, honest estimates, as ranges, of what to expect after deploying APV, built on stated assumptions. It is not a DPR, a bankability assessment or a site design.

Success means the user quickly understands the farm-versus-energy trade-off for their district, sees where it crosses the draft policy yield limit, and can share a short **Indicative Estimate Sheet** (PDF), with every number traceable to its source, method and evidence grade.

## Positioning

Existing tools are either US-centric techno-economic calculators (NREL's ADAM: US tax, MACRS, NSRDB, $/acre, no API) or shading/experiment designers with no finance or crop model. This product is built on Indian district data and Indian business models (PM-KUSUM Component A owner-operator, and land lease to a developer). It models crop response to shade by season (kharif, rabi, zaid), flags groundwater stress, and reports in ₹ per acre.

## Operating Context

- Unit of analysis is the **district** (~780, keyed by LGD codes). Finer resolution is out of scope because the data doesn't support it.
- Workflow: pick a district → review its context → choose business model (KUSUM-A or lease) → structure preset → crop rotation → finance inputs (pre-filled with state defaults) → explore GCR 0–50% against the draft 80% retention line → read the ranges → share an Indicative Estimate Sheet.
- Physics (energy per kWp, ground light fraction) is pre-computed per district for preset structure configurations. Crop response and finance run live in the API.
- Estimates inform early conversations, such as FPO discussions, lease talks, opportunity scoping and policy briefs. Not DPRs or financing decisions.

## Capabilities and Constraints

- Business models in v1: PM-KUSUM Component A (farmer/FPO owner, DISCOM tariff) and land lease (developer-owned; includes max affordable lease at a target IRR). KUSUM-C and C&I/open access are deferred.
- GCR is freely adjustable from 0.00 to 0.50 in steps of 0.05; GCR 0 is the open-field baseline.
- **Draft policy limit:** yield must stay at or above **80% of open-field yield** (at most 20% loss), as proposed by policymakers. It is shown as an editable reference line and an "allowed GCR range", not a hard block, because the policy isn't final.
- Results are **ranges** (low/central/high). Headline metrics: farm and energy income per acre (before/after), LER, yield retention, kWp per acre, payback, project IRR, max affordable lease. Equity IRR, DSCR and LCOE sit in an Advanced panel (P1).
- Crop shade response uses cited low/central/high parameters with **evidence grades** (A–D). The heat-relief uplift is off by default.
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
4. **Ranges, not false precision.** This is a knowledge tool: estimates are honest ranges with clear caveats, never DPR-grade claims.
5. **Indian context first.** Indian schemes, units (₹, acres, kharif/rabi), data sources and constraints come first; global defaults never do.
