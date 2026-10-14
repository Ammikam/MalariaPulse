"""MCP server: clinical surveillance data (weekly confirmed malaria cases per zone)."""
from mcp.server.fastmcp import FastMCP

from .. import data

mcp = FastMCP("malariapulse-clinical", log_level="WARNING")


@mcp.tool()
def list_zones() -> list[str]:
    """List all surveillance zones (micro-zones) the system covers."""
    return data.list_zones()


@mcp.tool()
def get_weekly_cases(zone: str, weeks: int = 12) -> list[dict]:
    """Get weekly confirmed malaria cases, tests done and test positivity for a zone.

    Args:
        zone: Zone name exactly as returned by list_zones.
        weeks: How many most-recent weeks to return (default 12).
    """
    return data.get_cases(zone, weeks)


if __name__ == "__main__":
    mcp.run()
