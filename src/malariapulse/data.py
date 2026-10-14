"""Tiny CSV data layer. Swap these loaders for DHIS2 / a database / real climate APIs later.

All shipped data is SYNTHETIC (see scripts/generate_synthetic_data.py).
"""
import csv
from functools import lru_cache

from .config import DATA_DIR


def _read(name: str) -> list[dict]:
    with open(DATA_DIR / name, newline="") as f:
        return list(csv.DictReader(f))


@lru_cache(maxsize=1)
def _cases() -> list[dict]:
    return _read("clinical_cases.csv")


@lru_cache(maxsize=1)
def _env() -> list[dict]:
    return _read("environment.csv")


@lru_cache(maxsize=1)
def _stock() -> list[dict]:
    return _read("stock.csv")


def list_zones() -> list[str]:
    seen: list[str] = []
    for r in _cases():
        if r["zone"] not in seen:
            seen.append(r["zone"])
    return seen


def get_cases(zone: str, weeks: int = 12) -> list[dict]:
    rows = [r for r in _cases() if r["zone"] == zone]
    if not rows:
        raise ValueError(f"Unknown zone: {zone}")
    rows = rows[-weeks:]
    return [
        {
            "week_start": r["week_start"],
            "confirmed_cases": int(r["confirmed_cases"]),
            "tests_done": int(r["tests_done"]),
            "test_positivity": round(int(r["confirmed_cases"]) / max(1, int(r["tests_done"])), 2),
            "population": int(r["population"]),
        }
        for r in rows
    ]


def get_env(zone: str, weeks: int = 12) -> list[dict]:
    rows = [r for r in _env() if r["zone"] == zone]
    if not rows:
        raise ValueError(f"Unknown zone: {zone}")
    rows = rows[-weeks:]
    return [
        {
            "week_start": r["week_start"],
            "rainfall_mm": float(r["rainfall_mm"]),
            "temp_c": float(r["temp_c"]),
            "humidity_pct": float(r["humidity_pct"]),
        }
        for r in rows
    ]


def get_stock(zone: str) -> list[dict]:
    rows = [r for r in _stock() if r["zone"] == zone]
    if not rows:
        raise ValueError(f"Unknown zone: {zone}")
    return [
        {
            "facility": r["facility"],
            "item": r["item"],
            "units_in_stock": int(r["units_in_stock"]),
            "avg_weekly_use": float(r["avg_weekly_use"]),
        }
        for r in rows
    ]
