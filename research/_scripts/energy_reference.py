"""D18 energy reference values: Global Solar Atlas PV output at 10 reference districts and at measured plants.

Usage: uv run --no-project --with numpy python -I energy_reference.py <research_dir>

1. Ten districts chosen to span India's climates (desert, dry coast, semi-arid south, foggy plains, humid tropics,
   wet north-east, central plateau, high mountains). Points are the same as the typical-year points
   (08_solar_weather/tmy/tmy_index.csv), so the energy model can be checked where it runs.
2. Measured plants (MEASURED below), each with its location and reported output, sampled the same way.
3. GSA PVOUT is AC energy per kWp of DC capacity for an open-field, optimally tilted fixed plant (kWh/kWp/day,
   x 365). Measured plants rated in MW AC are compared after multiplying PVOUT by an assumed DC/AC ratio.
   The calibrated typical year (D14) matches GSA annual GHI at the district points, so a gap between the energy
   model and these values points at the PV model, not the weather.
Writes 10_validation/energy_reference/energy_reference.csv and energy_reference_monthly.csv.
"""

import csv
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sample_gsa_districts import ZIP, sample

DISTRICTS = {
    "Jodhpur": "hot desert (BWh)",
    "Kachchh": "dry coast (BWh/BSh)",
    "Anantapur": "semi-arid south (BSh)",
    "Tumakuru": "semi-arid plateau (BSh)",
    "Ludhiana": "north-west plains, winter fog (Cwa)",
    "Lucknow": "central plains, winter haze (Cwa)",
    "Ernakulam": "humid tropics, long monsoon (Am)",
    "Kamrup": "wet north-east (Cwa)",
    "Rewa": "central plateau (Cwa)",
    "Leh Ladakh": "high-altitude cold desert (BWk)",
}
MEASURED = [
    {
        "plant": "ICAR-CAZRI agrivoltaic system, Jodhpur",
        "district": "Jodhpur",
        "lat": 26.25,
        "lon": 73.02,
        "capacity": "100 kWp DC",
        "basis": "kWp_dc",
        "kwh_per_kw_yr": 1248,
        "years": "2021",
        "source": "Poonia & Santra (2024), AgriVoltaics Conf. Proc. 1, doi:10.52825/agripv.v1i.601: 124,823 kWh in 2021",
        "quality": "measured (peer-reviewed); agrivoltaic layouts with part-density rows, so not a standard plant",
    },
    {
        "plant": "Pavagada Solar Park (2,050 MW AC)",
        "district": "Tumakuru",
        "lat": 14.25,
        "lon": 77.43,
        "capacity": "2,050 MW AC",
        "basis": "kw_ac",
        "kwh_per_kw_yr": 2174,
        "years": "2020-21 to 2025-26 (mean of 6 full years: 4,529, 4,464, 4,503, 4,599, 4,424, 4,219 MU)",
        "source": "KSPDCL, Solar Generation in Pavagada Solar Park, "
        "https://kspdcl.karnataka.gov.in/info-2/Solar+Generation+in+Pavagada+Solar+Park/en",
        "quality": "measured (state agency); AC basis, DC/AC ratio not published; output fell about 8% after 2023-24",
    },
    {
        "plant": "GIPCL solar fleet, Gujarat (262 MW)",
        "district": "Banaskantha",
        "lat": 24.2,
        "lon": 71.4,
        "capacity": "262 MW (AC basis assumed)",
        "basis": "kw_ac",
        "kwh_per_kw_yr": 2028,
        "years": "FY 2023-24 and 2024-25 (536.04 and 526.43 MU; CUF 23.29% and 22.94%)",
        "source": "Gujarat Industries Power Co., Plant Performance, https://www.gipcl.com/plant-performance.aspx",
        "quality": "measured (company disclosure); several sites whose locations the page does not give, taken as "
        "the north Gujarat solar parks (Charanka, Raghanesda), not verified; the point is approximate",
    },
    {
        "plant": "Cochin International Airport solar plants (about 40 MWp)",
        "district": "Ernakulam",
        "lat": 10.15,
        "lon": 76.40,
        "capacity": "about 40 MWp DC (2021)",
        "basis": "kWp_dc",
        "kwh_per_kw_yr": 1460,
        "years": "c. 2019-2021",
        "source": "press reports, e.g. Down to Earth, https://www.downtoearth.org.in/blog/energy/cochin-airport-powered-by-the-sun-67780: "
        "about 1.6 lakh kWh/day from 40 MWp; later reports give 2 lakh kWh/day from 50 MWp (also 1,460 kWh/kWp/yr)",
        "quality": "reported, not measured data: a rounded daily figure times 365; the 50 MWp total includes a "
        "12 MWp plant at Payyannur (Kannur district); weak",
    },
]
DC_AC = (1.25, 1.40)  # plausible range for Indian utility plants, used only to compare AC-rated plants


def main(research: Path) -> None:
    idx = {
        r["district"]: r
        for r in csv.DictReader((research / "08_solar_weather/tmy/tmy_index.csv").open(encoding="utf-8"))
    }
    pts = [{"lat": float(idx[d]["lat"]), "lon": float(idx[d]["lon"])} for d in DISTRICTS]
    pts += [{"lat": m["lat"], "lon": m["lon"]} for m in MEASURED]
    layers = ["PVOUT", "GHI", "OPTA"] + [f"monthly/PVOUT_{m:02d}" for m in range(1, 13)]
    with zipfile.ZipFile(research / "08_solar_weather/solar_atlas/raw/global_solar_atlas" / ZIP) as zf:
        val = {k: sample(zf, k, pts)[0] for k in layers}
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    out_dir = research / "10_validation" / "energy_reference"
    with (out_dir / "energy_reference.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["ref_id", "kind", "dist_lgd", "district", "state", "climate_or_plant", "lat", "lon",
                    "gsa_pvout_kwh_per_kwp_yr", "gsa_ghi_kwh_m2_yr", "gsa_opt_tilt_deg",
                    "measured_kwh_per_kw_yr", "measured_basis", "measured_years", "measured_vs_gsa",
                    "source", "quality"])  # fmt: skip
        for i, d in enumerate(DISTRICTS):
            r = idx[d]
            w.writerow([f"D{i + 1:02d}", "district_reference", r["dist_lgd"], d, r["state"], DISTRICTS[d], r["lat"],
                        r["lon"], round(val["PVOUT"][i] * 365), round(val["GHI"][i] * 365), round(val["OPTA"][i], 1),
                        "", "", "", "", "Global Solar Atlas 2.x (Solargis), India package",
                        "model reference (open-field fixed optimum tilt)"])  # fmt: skip
        for j, m in enumerate(MEASURED):
            i = len(DISTRICTS) + j
            pv = val["PVOUT"][i] * 365
            if m["basis"] == "kWp_dc":
                cmp_ = f"{m['kwh_per_kw_yr'] / pv:.2f} x GSA"
            else:
                cmp_ = (f"{m['kwh_per_kw_yr'] / (pv * DC_AC[1]):.2f}-{m['kwh_per_kw_yr'] / (pv * DC_AC[0]):.2f} x GSA "
                        f"(for DC/AC {DC_AC[0]}-{DC_AC[1]})")  # fmt: skip
            w.writerow([f"M{j + 1:02d}", "measured_plant", "", m["district"], "", m["plant"], m["lat"], m["lon"],
                        round(pv), round(val["GHI"][i] * 365), round(val["OPTA"][i], 1), m["kwh_per_kw_yr"],
                        m["basis"], m["years"], cmp_, m["source"], m["quality"]])  # fmt: skip
    with (out_dir / "energy_reference_monthly.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["ref_id", "district", "month", "gsa_pvout_kwh_per_kwp"])
        for i, d in enumerate(DISTRICTS):
            for mo in range(1, 13):
                w.writerow([f"D{i + 1:02d}", d, mo, round(val[f"monthly/PVOUT_{mo:02d}"][i] * days[mo - 1], 1)])
    print("written", out_dir)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
