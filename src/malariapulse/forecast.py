"""Transparent baseline risk model.

THIS IS A PLACEHOLDER FOR THE MODELLING TEAM'S REAL MODEL. Keep the function
signature of `assess_zone` and replace the body (or call your own model from it);
the MCP server and agents will keep working unchanged.

Signals (all explainable to a health officer):
  * case_signal    recent cases vs the previous 8 weeks (z-score)
  * growth_signal  ratio of recent to baseline weekly cases
  * env_signal     lagged rainfall vs the zone's own median, scaled by temperature suitability
"""
from statistics import mean, median, pstdev

from .config import HIGH_RISK, MODERATE_RISK


def _clip(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _slope(values: list[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    xs = list(range(n))
    xm, ym = mean(xs), mean(values)
    den = sum((x - xm) ** 2 for x in xs)
    return sum((x - xm) * (y - ym) for x, y in zip(xs, values)) / den if den else 0.0


def level_for(score: float) -> str:
    if score >= HIGH_RISK:
        return "high"
    if score >= MODERATE_RISK:
        return "moderate"
    return "low"


def assess_zone(cases: list[float], rainfall: list[float], temp: list[float]) -> dict:
    """cases/rainfall/temp are chronological weekly series (oldest first, >= 12 weeks)."""
    if len(cases) < 12 or len(rainfall) < 12 or len(temp) < 4:
        raise ValueError("Need at least 12 weeks of cases/rainfall and 4 weeks of temperature.")

    recent = mean(cases[-2:])
    base_window = cases[-10:-2]
    baseline = mean(base_window)
    sd = max(pstdev(base_window), 0.1 * baseline, 1.0)
    z = (recent - baseline) / sd
    growth = recent / baseline if baseline > 0 else 1.0

    rain_lag = mean(rainfall[-6:-2])
    rain_ref = median(rainfall) or 1.0
    temp_recent = mean(temp[-4:])
    temp_suit = 1.0 if 18 <= temp_recent <= 32 else 0.5

    case_signal = _clip(z / 4)
    growth_signal = _clip((growth - 1) / 0.8)
    env_signal = _clip((rain_lag / rain_ref - 0.8) / 1.2) * temp_suit

    score = round(0.45 * case_signal + 0.35 * growth_signal + 0.20 * env_signal, 3)

    slope = _slope(cases[-4:])
    projected = [max(0, round(cases[-1] + slope * k)) for k in (1, 2)]

    drivers = []
    if growth >= 1.25:
        drivers.append(f"Weekly cases up {round((growth - 1) * 100)}% vs the previous 8-week average")
    if z >= 2:
        drivers.append(f"Recent cases are {round(z, 1)} standard deviations above baseline")
    if env_signal >= 0.3:
        drivers.append("Rainfall 2-6 weeks ago was above this zone's normal, favouring mosquito breeding")
    if not drivers:
        drivers.append("No unusual rise in cases or environmental risk detected")

    return {
        "risk_score": score,
        "risk_level": level_for(score),
        "recent_weekly_cases": round(recent, 1),
        "baseline_weekly_cases": round(baseline, 1),
        "projected_cases_next_2_weeks": projected,
        "drivers": drivers,
        "model": "baseline-v0 (placeholder, not clinically validated)",
    }
