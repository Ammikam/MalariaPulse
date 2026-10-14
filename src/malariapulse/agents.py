"""The three collaborating agents.

Each agent has (a) a system prompt, (b) a restricted set of MCP servers it may use, and
(c) a `rules` implementation (deterministic, no API key) and an `llm` implementation
(Gemini decides which tools to call). Both run through the same MCP tools.

Human oversight: agents only PRODUCE PROPOSALS. A health officer approves, edits or rejects
each one in the review dashboard (app/review_app.py). Nothing is sent or ordered automatically.
"""
from . import llm
from .config import HIGH_RISK, MODERATE_RISK  # noqa: F401  (documented thresholds)
from .mcp_client import ToolHub

SURVEILLANCE_SERVERS = ["clinical", "environment", "forecast"]
SUPPLY_SERVERS = ["supply"]
COMMUNITY_SERVERS = ["outreach"]

SURVEILLANCE_PROMPT = """You are the Surveillance & Prediction Agent of a malaria early-warning system.
For EVERY zone: fetch its weekly cases and environmental data, then call assess_outbreak_risk.
Check data quality (missing weeks, odd test positivity) and mention concerns.
Return ONLY a JSON array. One object per zone with keys: zone, risk_score, risk_level, drivers (list),
projected_cases_next_2_weeks (list), recent_weekly_cases, baseline_weekly_cases, rationale (one sentence).
You provide an early-warning signal for a health officer, never a diagnosis or a certain prediction."""

SUPPLY_PROMPT = """You are the Supply & Resource Orchestration Agent. You are given high/moderate-risk zones.
For each zone: call compute_resupply_needs with a demand_multiplier based on the projected rise,
then for each item with a shortfall call find_surplus_stock to propose transfers from other zones.
Anything not covered by transfers becomes a restock request to the county medical store.
Return ONLY JSON: {"<zone>": {"demand_multiplier": number, "transfers": [{"from_zone","from_facility","to_facility","item","units"}],
"restock_requests": [{"facility","item","units","priority"}], "notes": string}}. These are drafts for human approval."""

COMMUNITY_PROMPT = """You are the Community Action & Intervention Agent. For each flagged zone call draft_advisory
for audiences 'chw' and 'residents' in languages 'en' and 'sw'. You may only use the drafting tools.
Return ONLY JSON: {"<zone>": [{"audience","language","text"}]}. All messages are drafts that a human must approve."""


# ----------------------------- Surveillance -----------------------------
async def surveillance_agent(hub: ToolHub, mode: str) -> list[dict]:
    hub.current_agent = "surveillance"
    if mode == "llm":
        try:
            text, _ = await llm.run_agent(hub, SURVEILLANCE_PROMPT, "Assess all zones now.", SURVEILLANCE_SERVERS)
            return llm.parse_json(text)
        except Exception as exc:
            hub.calls.append({"agent": "surveillance", "tool": "(llm failed, using rules)", "args": {"error": str(exc)}})
    results = []
    for zone in await hub.call("list_zones"):
        cases = await hub.call("get_weekly_cases", zone=zone, weeks=12)
        env = await hub.call("get_environment", zone=zone, weeks=12)
        risk = await hub.call("assess_outbreak_risk", zone=zone)
        quality = []
        if len(cases) < 12 or len(env) < 12:
            quality.append("Fewer than 12 weeks of data available")
        risk["rationale"] = "; ".join(risk["drivers"]) + (f". Data notes: {'; '.join(quality)}" if quality else "")
        results.append(risk)
    return results


# ----------------------------- Supply -----------------------------
async def supply_agent(hub: ToolHub, mode: str, flagged: list[dict]) -> dict:
    hub.current_agent = "supply"
    if not flagged:
        return {}
    if mode == "llm":
        try:
            task = "Plan resupply for these zones:\n" + llm.json.dumps(flagged)
            text, _ = await llm.run_agent(hub, SUPPLY_PROMPT, task, SUPPLY_SERVERS)
            return llm.parse_json(text)
        except Exception as exc:
            hub.calls.append({"agent": "supply", "tool": "(llm failed, using rules)", "args": {"error": str(exc)}})
    plans = {}
    for a in flagged:
        zone = a["zone"]
        recent = max(a["recent_weekly_cases"], 1)
        multiplier = round(min(3.0, max(1.0, a["projected_cases_next_2_weeks"][-1] / recent)), 2)
        needs = await hub.call("compute_resupply_needs", zone=zone, demand_multiplier=multiplier, target_weeks_cover=3.0)
        donors_by_item: dict[str, list[dict]] = {}
        transfers, requests = [], []
        for n in needs:
            short = n["shortfall_units"]
            if short <= 0:
                continue
            if n["item"] not in donors_by_item:
                donors_by_item[n["item"]] = await hub.call("find_surplus_stock", item=n["item"], exclude_zone=zone)
            for d in donors_by_item[n["item"]]:
                if short <= 0:
                    break
                take = min(short, d["surplus_units"])
                if take > 0:
                    transfers.append({
                        "from_zone": d["zone"], "from_facility": d["facility"],
                        "to_facility": n["facility"], "item": n["item"], "units": take,
                    })
                    d["surplus_units"] -= take
                    short -= take
            if short > 0:
                requests.append({"facility": n["facility"], "item": n["item"], "units": short, "priority": n["priority"]})
        plans[zone] = {
            "demand_multiplier": multiplier,
            "transfers": transfers,
            "restock_requests": requests,
            "notes": "Draft only. Confirm quantities with facility in-charges before moving stock.",
        }
    return plans


# ----------------------------- Community -----------------------------
async def community_agent(hub: ToolHub, mode: str, flagged: list[dict]) -> dict:
    hub.current_agent = "community"
    if not flagged:
        return {}
    if mode == "llm":
        try:
            task = "Draft advisories for these zones:\n" + llm.json.dumps(flagged)
            text, _ = await llm.run_agent(hub, COMMUNITY_PROMPT, task, COMMUNITY_SERVERS)
            return llm.parse_json(text)
        except Exception as exc:
            hub.calls.append({"agent": "community", "tool": "(llm failed, using rules)", "args": {"error": str(exc)}})
    out = {}
    for a in flagged:
        drafts = []
        for audience in ("chw", "residents"):
            for language in ("en", "sw"):
                d = await hub.call("draft_advisory", zone=a["zone"], risk_level=a["risk_level"],
                                   language=language, audience=audience)
                drafts.append({"audience": audience, "language": language, "text": d["text"]})
        out[a["zone"]] = drafts
    return out
