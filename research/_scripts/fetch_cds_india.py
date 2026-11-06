"""Request India-wide climate and solar data from the Copernicus Climate Data Store (CDS).

Needs YOUR CDS account (the Claude session did not create or use one):
  1. Register at https://cds.climate.copernicus.eu and copy your API key into ~/.cdsapirc
     (format: https://cds.climate.copernicus.eu/how-to-api).
  2. On each dataset's page, open "Download data" and accept its licence once (tick box at the bottom).
  3. pip install "cdsapi>=0.7"
  4. python fetch_cds_india.py <research_dir> [era5land|agera5|all]

Files land in the git-ignored raw/ folders listed below. Record each download in the matching
SOURCE_copernicus_cds.md (accessed date, licence version).
"""

import sys
from pathlib import Path

import cdsapi

INDIA_AREA = [38, 68, 6, 98]  # North, West, South, East (degrees); covers mainland India + islands buffer
YEARS = [str(y) for y in range(1991, 2021)]
MONTHS = [f"{m:02d}" for m in range(1, 13)]


def era5_land_monthly(c: cdsapi.Client, out: Path) -> None:
    """ERA5-Land monthly means, 0.1 deg, 1991-2020: temperature, precipitation, solar radiation (D02, D03, D14)."""
    out.mkdir(parents=True, exist_ok=True)
    c.retrieve(
        "reanalysis-era5-land-monthly-means",
        {
            "product_type": ["monthly_averaged_reanalysis"],
            "variable": ["2m_temperature", "total_precipitation", "surface_solar_radiation_downwards"],
            "year": YEARS,
            "month": MONTHS,
            "time": ["00:00"],
            "area": INDIA_AREA,
            "data_format": "netcdf",
            "download_format": "unarchived",
        },
        str(out / "era5land_monthly_1991-2020_t2m_tp_ssrd_india.nc"),
    )


def agera5_daily(c: cdsapi.Client, out: Path, year: str = "2020") -> None:
    """AgERA5 daily agro-met indicators, 0.1 deg (one year as a trial; loop years as needed) (D02, D03, D14)."""
    out.mkdir(parents=True, exist_ok=True)
    for variable, stats in [
        ("2m_temperature", ["24_hour_maximum", "24_hour_minimum", "24_hour_mean"]),
        ("solar_radiation_flux", None),
        ("precipitation_flux", None),
    ]:
        req = {
            "variable": variable,
            "year": [year],
            "month": MONTHS,
            "day": [f"{d:02d}" for d in range(1, 32)],
            "version": "2_0",
            "area": INDIA_AREA,
        }
        if stats:
            req["statistic"] = stats
        c.retrieve("sis-agrometeorological-indicators", req, str(out / f"agera5_{variable}_{year}_india.zip"))


def main() -> None:
    research = Path(sys.argv[1])
    which = sys.argv[2] if len(sys.argv) > 2 else "era5land"
    c = cdsapi.Client()
    if which in ("era5land", "all"):
        era5_land_monthly(c, research / "08_solar_weather" / "tmy" / "raw" / "cds")
    if which in ("agera5", "all"):
        agera5_daily(c, research / "01_agro_climate" / "temperature" / "raw" / "agera5")


if __name__ == "__main__":
    main()
