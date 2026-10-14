"""Orchestrates the three agents and stores proposals for human review.

Usage:
  python -m malariapulse.pipeline                 # rules mode (no API key needed)
  python -m malariapulse.pipeline --mode llm      # Gemini-driven agents (needs GEMINI_API_KEY)
  python -m malariapulse.pipeline --no-save       # dry run, do not write to the review queue
"""
import argparse
import asyncio
from datetime import datetime, timezone

from . import store
from .agents import community_agent, supply_agent, surveillance_agent
from .mcp_client import ToolHub


async def run_pipeline(mode: str = "rules", save: bool = True) -> dict:
    async with ToolHub() as hub:
        assessments = await surveillance_agent(hub, mode)
        flagged = [a for a in assessments if a["risk_level"] in ("high", "moderate")]
        # The Supply and Community agents are triggered only for flagged zones.
        supply = await supply_agent(hub, mode, flagged)
        community = await community_agent(hub, mode, flagged)
        calls = list(hub.calls)

    generated_at = datetime.now(timezone.utc).isoformat()
    proposals = [
        {
            "zone": a["zone"],
            "risk": a,
            "supply_plan": supply.get(a["zone"], {}),
            "advisories": community.get(a["zone"], []),
            "mode": mode,
            "generated_at": generated_at,
            "agent_calls": [c for c in calls],
        }
        for a in flagged
    ]
    ids = store.save_proposals(proposals) if save and proposals else []
    return {"assessments": assessments, "proposals": proposals, "proposal_ids": ids, "tool_calls": calls}


def main():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    ap = argparse.ArgumentParser(description="Run the MalariaPulse agent pipeline")
    ap.add_argument("--mode", choices=["rules", "llm"], default="rules")
    ap.add_argument("--no-save", action="store_true")
    args = ap.parse_args()

    out = asyncio.run(run_pipeline(args.mode, save=not args.no_save))
    print(f"\nMalariaPulse run ({args.mode} mode): {len(out['tool_calls'])} MCP tool calls\n")
    print(f"{'Zone':16}{'Score':>7}  {'Level':10} Drivers")
    for a in sorted(out["assessments"], key=lambda x: -x["risk_score"]):
        print(f"{a['zone']:16}{a['risk_score']:>7.2f}  {a['risk_level']:10} {a['drivers'][0]}")
    print(f"\n{len(out['proposals'])} proposal(s) queued for human review. "
          f"Run: streamlit run app/review_app.py" if out["proposals"] else "\nNo zones need action.")


if __name__ == "__main__":
    main()
