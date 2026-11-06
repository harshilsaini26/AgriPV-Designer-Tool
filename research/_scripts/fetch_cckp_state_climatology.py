"""Fetch ERA5 1991-2020 monthly climatology for India and its states from the
World Bank Climate Change Knowledge Portal (CCKP) API and write tidy CSVs.

Usage: python -I fetch_cckp_state_climatology.py <research_dir>
"""

import csv
import json
import sys
import urllib.request
from pathlib import Path

API = (
    "https://cckpapi.worldbank.org/cckp/v1/era5-x0.25_climatology_{v}_climatology_monthly_"
    "1991-2020_mean_historical_era5_x0.25_mean/{g}?_format=json"
)
STATES = {
    "IND": "India",
    "IND.1151": "Andaman and Nicobar Islands",
    "IND.1152": "Andhra Pradesh",
    "IND.1153": "Arunachal Pradesh",
    "IND.1154": "Assam",
    "IND.1155": "Bihar",
    "IND.1156": "Chandigarh",
    "IND.1157": "Chhattisgarh",
    "IND.1158": "Dadra and Nagar Haveli",
    "IND.1159": "Daman and Diu",
    "IND.11510": "Delhi",
    "IND.11511": "Goa",
    "IND.11512": "Gujarat",
    "IND.11513": "Haryana",
    "IND.11514": "Himachal Pradesh",
    "IND.11515": "Jammu and Kashmir",
    "IND.11516": "Jharkhand",
    "IND.11517": "Karnataka",
    "IND.11518": "Kerala",
    "IND.11519": "Lakshadweep",
    "IND.11520": "Madhya Pradesh",
    "IND.11521": "Maharashtra",
    "IND.11522": "Manipur",
    "IND.11523": "Meghalaya",
    "IND.11524": "Mizoram",
    "IND.11525": "Nagaland",
    "IND.11526": "Odisha",
    "IND.11527": "Puducherry",
    "IND.11528": "Punjab",
    "IND.11529": "Rajasthan",
    "IND.11530": "Sikkim",
    "IND.11531": "Tamil Nadu",
    "IND.11532": "Telangana",
    "IND.11533": "Tripura",
    "IND.11534": "Uttar Pradesh",
    "IND.11535": "Uttarakhand",
    "IND.11536": "West Bengal",
}
GROUPS = {
    "temperature": ["tas", "tasmax", "tasmin", "hd35", "hd40"],
    "rainfall": ["pr"],
}


def get(var: str) -> dict:
    url = API.format(v=var, g=",".join(STATES))
    req = urllib.request.Request(url, headers={"User-Agent": "agripv-lab-research/0.1"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)["data"]


def main(research: Path) -> None:
    for folder, variables in GROUPS.items():
        out = research / "01_agro_climate" / folder
        raw = out / "raw"
        raw.mkdir(parents=True, exist_ok=True)
        rows = {}
        for v in variables:
            data = get(v)
            (raw / f"cckp_era5_1991-2020_{v}.json").write_text(json.dumps(data), encoding="utf-8")
            series = data.get(v, data)  # single-variable responses are not nested by variable
            for geo, months in series.items():
                for key, val in months.items():
                    m = int(key.split("-")[1])
                    rows.setdefault((geo, m), {})[v] = val
        path = out / "cckp_era5_state_climatology_1991-2020.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["cckp_geocode", "state_name", "month", *variables])
            for geo, m in sorted(rows, key=lambda k: (list(STATES).index(k[0]), k[1])):
                w.writerow([geo, STATES[geo], m, *[rows[(geo, m)].get(v, "") for v in variables]])
        print(path, len(rows), "rows")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
