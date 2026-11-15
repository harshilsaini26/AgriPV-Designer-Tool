"""Check a deployment against the slice spec's targets (spec §8). Standard library only.

Usage: python scripts/check_deployment.py <base_url>

Requests the home page, a deep link, the health endpoint, then the sweep once ("first", which may hit a cold
start) and 20 more times ("warm"). Prints a table and exits 1 unless every check passes.
"""

import json
import statistics
import sys
import time
import urllib.error
import urllib.request

FIRST_LIMIT_S = 8.0
WARM_P95_LIMIT_S = 1.5
WARM_RUNS = 20
EXPECTED_PACKS = 785
SWEEP_PATH = "/api/_probe/sweep?district_id=107_jodhpur"
SWEEP_BODY: dict | None = None  # set when the sweep is a POST (plan Task 6)


def fetch(url: str, body: dict | None = None, timeout: float = 60.0) -> tuple[int, str, float]:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if data else {"Accept": "text/html,application/json"}
    req = urllib.request.Request(url, data=data, headers=headers)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            text = r.read().decode("utf-8", errors="replace")
            status = r.status
    except urllib.error.HTTPError as e:
        text, status = e.read().decode("utf-8", errors="replace"), e.code
    except (urllib.error.URLError, TimeoutError) as e:
        return 0, repr(e), time.perf_counter() - t0
    return status, text, time.perf_counter() - t0


def main(base: str) -> int:
    base = base.rstrip("/")
    rows: list[tuple[str, bool, str]] = []

    for name, path in (("home page", "/"), ("deep link", "/model/107_jodhpur")):
        status, text, _ = fetch(base + path)
        rows.append((name, status == 200 and "AgriPV Lab" in text, f"HTTP {status}"))

    status, text, _ = fetch(base + "/api/health")
    try:
        health = json.loads(text)
    except json.JSONDecodeError:
        health = {}
    ok = status == 200 and health.get("status") == "ok" and health.get("weather_packs") == EXPECTED_PACKS
    rows.append(
        ("health", ok, f"HTTP {status}, {health.get('weather_packs')} packs, Python {health.get('python')}")
    )

    status, text, first = fetch(base + SWEEP_PATH, SWEEP_BODY)
    engine = ""
    if status == 200:
        engine = f", engine {json.loads(text).get('engine_ms')} ms"
    rows.append(
        ("sweep, first", status == 200 and first <= FIRST_LIMIT_S, f"HTTP {status}, {first:.2f} s{engine}")
    )

    times, statuses = [], set()
    for _ in range(WARM_RUNS):
        status, _, t = fetch(base + SWEEP_PATH, SWEEP_BODY)
        statuses.add(status)
        times.append(t)
    p95 = statistics.quantiles(times, n=20)[-1]
    rows.append(
        (
            "sweep, warm p95",
            statuses == {200} and p95 <= WARM_P95_LIMIT_S,
            f"{p95:.2f} s (median {statistics.median(times):.2f} s, statuses {sorted(statuses)})",
        )
    )

    width = max(len(r[0]) for r in rows)
    for name, passed, detail in rows:
        print(f"{'PASS' if passed else 'FAIL'}  {name:<{width}}  {detail}")
    return 0 if all(r[1] for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
