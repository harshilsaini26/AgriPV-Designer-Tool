"""The AgriPV Lab API (model-slice spec §6)."""

import platform

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from backend._paths import REPO_ROOT
from backend.data import (
    PREVIEW_NOTICE,
    WEATHER_DIR,
    default_tilt_deg,
    economics_for,
    example_rotation_for,
    load_app_data,
    tariff_for,
)
from backend.schemas import District, DistrictListItem, Health, Meta, SweepRequest, SweepResponse
from backend.service import InputError, run_sweep_request

WEB_DIST = REPO_ROOT / "web" / "dist"
SEASONS = ["kharif", "rabi", "zaid"]
POLICY = {"default": 0.8, "min": 0.5, "max": 1.0, "step": 0.05}

app = FastAPI(title="AgriPV Lab API", version="0.1.0")


@app.get("/api/health", response_model=Health)
def health() -> dict:
    return {
        "status": "ok",
        "weather_packs": len(list(WEATHER_DIR.glob("*.npz"))),
        "python": platform.python_version(),
        "data_version": load_app_data().manifest["data_version"],
    }


@app.get("/api/meta", response_model=Meta)
def meta() -> dict:
    data = load_app_data()
    return {
        "data_version": data.manifest["data_version"],
        "preview_notice": PREVIEW_NOTICE,
        "presets": data.structures["presets"],
        "modules": data.structures["modules"],
        "limits": data.structures["limits"],
        "crops": list(data.crops.values()),
        "seasons": SEASONS,
        "policy": POLICY,
        "retention_bases": ["per_acre_of_land", "per_cropped_area"],
        "business_models": ["kusum_a", "lease"],
        "assumptions": data.finance["assumptions"],
        "sources": data.sources,
    }


@app.get("/api/districts", response_model=list[DistrictListItem])
def districts() -> list[dict]:
    return [
        {"id": d["id"], "name": d["name"], "state": d["state"]} for d in load_app_data().districts.values()
    ]


@app.get(
    "/api/district/{district_id}",
    response_model=District,
    response_model_exclude_none=True,
)
def district(district_id: str) -> dict:
    data = load_app_data()
    entry = data.districts.get(district_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="unknown district")
    state = entry["state"]
    economics = {}
    for crop_id in data.crops:
        figures = economics_for(data, state, crop_id)
        if figures is not None:
            economics[crop_id] = figures
    return {
        **entry,
        "default_tilt_deg": default_tilt_deg(entry),
        "tariff": tariff_for(data, state),
        "economics": economics,
        "example_rotation": example_rotation_for(data, state),
    }


@app.post("/api/sweep", response_model=SweepResponse)
def sweep(req: SweepRequest) -> dict:
    try:
        return run_sweep_request(req)
    except LookupError:
        raise HTTPException(status_code=404, detail="unknown district") from None


@app.exception_handler(InputError)
def input_error(_: Request, exc: InputError) -> JSONResponse:
    detail = [{"loc": ["body", *exc.loc], "msg": exc.message, "type": "value_error"}]
    return JSONResponse(status_code=422, content={"detail": detail})


if WEB_DIST.is_dir():
    # every path that is not an API route or a built file gets index.html, so deep links load the app
    app.frontend("/", directory=str(WEB_DIST), fallback="index.html")
