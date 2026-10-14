from malariapulse import data, forecast


def _series(zone):
    c = [r["confirmed_cases"] for r in data.get_cases(zone, 52)]
    e = data.get_env(zone, 52)
    return c, [r["rainfall_mm"] for r in e], [r["temp_c"] for r in e]


def test_outbreak_zones_flagged_high():
    for zone in ("Lakeview", "Riverbend"):
        assert forecast.assess_zone(*_series(zone))["risk_level"] == "high"


def test_stable_zones_not_high():
    for zone in ("Savanna East", "Coastal Flats", "Dry Plains"):
        assert forecast.assess_zone(*_series(zone))["risk_level"] != "high"


def test_rejects_short_series():
    import pytest
    with pytest.raises(ValueError):
        forecast.assess_zone([1] * 5, [1] * 5, [25] * 5)
