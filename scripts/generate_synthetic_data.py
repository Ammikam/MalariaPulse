"""Generate SYNTHETIC malaria surveillance data. No real patient or facility data.

Writes three CSVs to data/:
  clinical_cases.csv  weekly case counts per zone
  environment.csv     weekly rainfall / temperature / humidity per zone
  stock.csv           current clinic stock of malaria commodities

Two zones (Lakeview, Riverbend) get an injected rising trend in the most recent
weeks so the demo has something to detect.

Run:  python scripts/generate_synthetic_data.py
"""
import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
WEEKS = 52
LAST_WEEK_START = date(2026, 10, 5)  # Monday of the most recent week
OUT = Path(__file__).resolve().parents[1] / "data"

# zone: (population, base weekly cases, mean temp C, rain scale, outbreak injected?)
ZONES = {
    "Lakeview":       (42000, 60, 27.0, 1.2, True),
    "Riverbend":      (35000, 48, 26.0, 1.1, True),
    "Highland Ridge": (28000, 12, 19.5, 1.0, False),
    "Savanna East":   (31000, 30, 25.0, 0.8, False),
    "Coastal Flats":  (39000, 44, 28.0, 1.3, False),
    "Dry Plains":     (22000, 14, 29.0, 0.4, False),
}

# zone: [(facility, share of the zone's caseload)]
FACILITIES = {
    "Lakeview":       [("Lakeview Health Centre", 0.6), ("Pier Dispensary", 0.4)],
    "Riverbend":      [("Riverbend Clinic", 0.65), ("Ford Road Dispensary", 0.35)],
    "Highland Ridge": [("Ridge Health Post", 1.0)],
    "Savanna East":   [("Savanna Health Centre", 1.0)],
    "Coastal Flats":  [("Flats Health Centre", 0.6), ("Harbour Dispensary", 0.4)],
    "Dry Plains":     [("Plains Dispensary", 1.0)],
}

# item: (units needed per confirmed case, typical weeks of cover)
ITEMS = {
    "RDT kits": (1.4, 3.0),
    "ACT treatments": (0.9, 3.0),
    "Bed nets": (0.5, 6.0),
}


def season(week_start: date) -> float:
    """Two rainy seasons: long rains (Mar-May) and short rains (Oct-Dec)."""
    doy = week_start.timetuple().tm_yday
    long_rains = math.exp(-((doy - 110) ** 2) / (2 * 25 ** 2))
    short_rains = 0.7 * math.exp(-((doy - 305) ** 2) / (2 * 22 ** 2))
    return long_rains + short_rains


def main():
    rng = random.Random(SEED)
    OUT.mkdir(exist_ok=True)
    weeks = [LAST_WEEK_START - timedelta(weeks=WEEKS - 1 - i) for i in range(WEEKS)]

    env_rows, case_rows, last_cases = [], [], {}
    for zone, (pop, base, temp, rain_scale, outbreak) in ZONES.items():
        rain_hist = []
        for i, w in enumerate(weeks):
            s = season(w)
            rain = max(0.0, rng.gauss(10 + 85 * s * rain_scale, 8))
            t = temp + 2.0 * math.sin((i / 52) * 2 * math.pi) + rng.gauss(0, 0.6)
            hum = min(95, max(25, 45 + 0.35 * rain + rng.gauss(0, 4)))
            rain_hist.append(rain)
            env_rows.append([zone, w.isoformat(), round(rain, 1), round(t, 1), round(hum, 1)])

            lagged = rain_hist[max(0, i - 4):max(1, i - 1)]
            lag_rain = sum(lagged) / len(lagged)
            temp_ok = 1.0 if 20 <= t <= 32 else 0.6
            expected = base * (0.6 + lag_rain / 60) * temp_ok
            cases = max(0, rng.gauss(expected, max(2, expected * 0.12)))
            if outbreak and i >= WEEKS - 5:
                cases *= 1 + 0.35 * (i - (WEEKS - 6))  # rising trend in last 5 weeks
            tests = int(cases * rng.uniform(1.8, 2.3))
            case_rows.append([zone, w.isoformat(), int(round(cases)), tests, pop])
            if i == WEEKS - 1:
                last_cases[zone] = cases

    stock_rows = []
    for zone, facs in FACILITIES.items():
        for fac, share in facs:
            weekly = last_cases[zone] * share
            for item, (per_case, cover_weeks) in ITEMS.items():
                use = weekly * per_case
                # outbreak zones are intentionally under-stocked
                cover = cover_weeks * (0.45 if ZONES[zone][4] else rng.uniform(0.9, 1.4))
                stock_rows.append([zone, fac, item, int(use * cover), round(use, 1)])

    def write(name, header, rows):
        with open(OUT / name, "w", newline="") as f:
            wr = csv.writer(f)
            wr.writerow(header)
            wr.writerows(rows)

    write("clinical_cases.csv", ["zone", "week_start", "confirmed_cases", "tests_done", "population"], case_rows)
    write("environment.csv", ["zone", "week_start", "rainfall_mm", "temp_c", "humidity_pct"], env_rows)
    write("stock.csv", ["zone", "facility", "item", "units_in_stock", "avg_weekly_use"], stock_rows)
    print(f"Wrote synthetic data to {OUT}")


if __name__ == "__main__":
    main()
