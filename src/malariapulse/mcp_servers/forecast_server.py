"""MCP server: outbreak risk model. Wraps forecast.assess_zone (replace with the real model)."""
from mcp.server.fastmcp import FastMCP

from .. import data, forecast

mcp = FastMCP("malariapulse-forecast", log_level="WARNING")


@mcp.tool()
def assess_outbreak_risk(zone: str) -> dict:
    """Score the malaria outbreak risk for one zone (0-1) with a level, drivers and a 2-week projection.

    Uses the last 52 weeks of clinical and environmental data. The output is an early-warning
    signal for a health officer to review, not a diagnosis or a certain prediction.

    Args:
        zone: Zone name exactly as returned by list_zones.
    """
    cases = [r["confirmed_cases"] for r in data.get_cases(zone, 52)]
    env = data.get_env(zone, 52)
    result = forecast.assess_zone(
        cases, [r["rainfall_mm"] for r in env], [r["temp_c"] for r in env]
    )
    return {"zone": zone, **result}


if __name__ == "__main__":
    mcp.run()
