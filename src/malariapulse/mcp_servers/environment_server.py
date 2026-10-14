"""MCP server: environmental drivers (rainfall, temperature, humidity) per zone.

Shipped with synthetic data. To use real data, call NASA POWER / Open-Meteo / CHIRPS
inside get_environment() instead of reading the CSV.
"""
from mcp.server.fastmcp import FastMCP

from .. import data

mcp = FastMCP("malariapulse-environment", log_level="WARNING")


@mcp.tool()
def get_environment(zone: str, weeks: int = 12) -> list[dict]:
    """Get weekly rainfall (mm), mean temperature (C) and humidity (%) for a zone.

    Args:
        zone: Zone name exactly as returned by list_zones.
        weeks: How many most-recent weeks to return (default 12).
    """
    return data.get_env(zone, weeks)


if __name__ == "__main__":
    mcp.run()
