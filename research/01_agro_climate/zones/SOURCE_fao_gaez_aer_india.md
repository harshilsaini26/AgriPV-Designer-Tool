# SOURCE: Agro-Ecological (Sub)regions of India, FAO GAEZ v4 data portal (NBSS&LUP 1996)

| Field | Value |
|---|---|
| Dataset ID | D01 |
| Publisher / owner | Original map: ICAR National Bureau of Soil Survey & Land Use Planning (NBSS&LUP), 1996. Hosted by FAO on the GAEZ v4 portal (ArcGIS item owner `boneill_hqfao`) |
| Dataset name and version | "Agro Ecological Subregions of India", ArcGIS item `5aae0d9b7b0542c4845026ec68cad442`, created 2024-05-21, modified 2024-05-28 |
| URL / access route | Page: https://gaez.fao.org/datasets/hqfao::agro-ecological-subregions-of-india/about. Data: `https://services5.arcgis.com/sjP4Ugu5s0dZWLjd/arcgis/rest/services/Agro_Ecological_Subregions_of_India/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=geojson` |
| Accessed on (YYYY-MM-DD) | 2026-11-06 |
| Reference year(s) covered | 1996 delineation |
| Spatial coverage | All-India |
| Spatial unit or resolution | 20 polygons, one per agro-ecological region. NBSS&LUP adjusted the boundaries to district boundaries |
| Temporal resolution | One-off |
| Licence | Not stated. Access information reads only "As per ICAR, New Delhi" |
| OK for a public open-source app? | **Unknown.** Do not redistribute the geometry until ICAR / NBSS&LUP terms are confirmed. A derived district-to-AER lookup is lower risk but still needs confirmation |
| Required attribution text | "Agro-ecological regions: ICAR-NBSS&LUP (1996), via FAO GAEZ v4 data portal" |
| Citation | Sehgal, J., Mandal, D. K., Mandal, C. & Vadivelu, S. (1992). Agro-Ecological Regions of India. NBSS&LUP Publ. 24, ICAR, Nagpur. Accessed via the FAO GAEZ v4 data portal |
| Files in this folder | Git-ignored: `raw/fao_gaez_aesr_india.geojson` (11.2 MB, EPSG:4326), `raw/fao_gaez_item.json` (ArcGIS item metadata incl. description) |
| Units and key column meanings | `AEZ`: full region name (e.g. "WESTERN HIMALAYAS COLD ARID ECO-REGION"). There is no numeric code field; the 1–20 numbering exists only in the item description |
| Known caveats and gaps | (1) **Despite its title, the layer holds the 20 agro-ecological regions, not the 60 sub-regions.** The 60 AESRs need another source (NBSS&LUP publication or Bhuvan). (2) Names contain typos ("EGO-REGION", "DECCAN PLATU", "SUBAUMID") and double spaces, so normalise them before joining. (3) The 1996 delineation predates many district splits. (4) The 15 Planning Commission agro-climatic zones (also part of D01) are a different scheme and still need a source |
| Processing notes | None yet. Planned: add a numeric `aer_code` (1–20) following the description's order, then intersect with D00 district polygons to get each district's dominant AER and its area share |
