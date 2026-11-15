"""The district list for search and lookup, from the weather-pack index."""

from pipeline.appdata.states import canonical_state


def build_districts(index_entries: list[dict]) -> list[dict]:
    """One entry per weather pack; `id` is the pack's file stem (district codes alone are not unique)."""
    out, seen = [], set()
    for e in index_entries:
        district_id = e["file"].removesuffix(".npz")
        if district_id in seen:
            raise ValueError(f"duplicate district id {district_id}")
        seen.add(district_id)
        out.append(
            {
                "id": district_id,
                "lgd": str(e["dist_lgd"]),
                "name": e["district"],
                "state": canonical_state(e["state"]),
                "lat": e["lat"],
                "lon": e["lon"],
                "elevation_m": e["elevation_m"],
                "optimum_tilt_deg": e["optimum_tilt_deg"],
            }
        )
    return sorted(out, key=lambda d: (d["state"], d["name"], d["id"]))
