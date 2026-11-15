"""The AgriPV Lab API."""

import platform

from fastapi import FastAPI, HTTPException

from backend._paths import REPO_ROOT

WEATHER_DIR = REPO_ROOT / "data" / "weather"
WEB_DIST = REPO_ROOT / "web" / "dist"

app = FastAPI(title="AgriPV Lab API", version="0.1.0")


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "weather_packs": len(list(WEATHER_DIR.glob("*.npz"))),
        "python": platform.python_version(),
    }


@app.get("/api/_probe/sweep")
def probe_sweep(district_id: str) -> dict:
    from backend._probe import run_probe

    pack = WEATHER_DIR / f"{district_id}.npz"
    if "/" in district_id or "\\" in district_id or not pack.is_file():
        raise HTTPException(status_code=404, detail="unknown district")
    return {"district_id": district_id, **run_probe(pack)}


if WEB_DIST.is_dir():
    # every path that is not an API route or a built file gets index.html, so deep links load the app
    app.frontend("/", directory=str(WEB_DIST), fallback="index.html")
