"""MCP server: clinic stock and resupply planning (RDT kits, ACT treatments, bed nets)."""
from mcp.server.fastmcp import FastMCP

from .. import data

mcp = FastMCP("malariapulse-supply", log_level="WARNING")


@mcp.tool()
def get_stock(zone: str) -> list[dict]:
    """Get current stock and average weekly use of malaria commodities at each facility in a zone.

    Args:
        zone: Zone name exactly as returned by list_zones.
    """
    return data.get_stock(zone)


@mcp.tool()
def compute_resupply_needs(zone: str, demand_multiplier: float = 1.0, target_weeks_cover: float = 3.0) -> list[dict]:
    """Compute per-facility shortfalls if demand rises, sorted by urgency.

    Args:
        zone: Zone name exactly as returned by list_zones.
        demand_multiplier: Expected demand relative to normal (e.g. 1.5 = 50% more cases).
        target_weeks_cover: Weeks of stock the facility should hold.
    """
    out = []
    for r in data.get_stock(zone):
        weekly = r["avg_weekly_use"] * demand_multiplier
        cover = r["units_in_stock"] / weekly if weekly else 99.0
        shortfall = max(0, round(weekly * target_weeks_cover - r["units_in_stock"]))
        if r["item"] == "Bed nets" or shortfall == 0:
            priority = "normal"
        else:
            priority = "critical" if cover < 1 else "high" if cover < 2 else "normal"
        out.append({
            "facility": r["facility"],
            "item": r["item"],
            "units_in_stock": r["units_in_stock"],
            "weeks_of_cover_now": round(cover, 1),
            "shortfall_units": shortfall,
            "priority": priority,
        })
    order = {"critical": 0, "high": 1, "normal": 2}
    return sorted(out, key=lambda x: (order[x["priority"]], -x["shortfall_units"]))


@mcp.tool()
def find_surplus_stock(item: str, exclude_zone: str, keep_weeks_cover: float = 4.5) -> list[dict]:
    """Find facilities in OTHER zones holding more of an item than they need, as transfer donors.

    Args:
        item: One of 'RDT kits', 'ACT treatments', 'Bed nets'.
        exclude_zone: The zone that needs stock (donors come from elsewhere).
        keep_weeks_cover: Weeks of cover a donor must keep for itself.
    """
    out = []
    for zone in data.list_zones():
        if zone == exclude_zone:
            continue
        for r in data.get_stock(zone):
            if r["item"] != item:
                continue
            surplus = int(r["units_in_stock"] - r["avg_weekly_use"] * keep_weeks_cover)
            if surplus > 0:
                out.append({"zone": zone, "facility": r["facility"], "item": item, "surplus_units": surplus})
    return sorted(out, key=lambda x: -x["surplus_units"])


if __name__ == "__main__":
    mcp.run()
