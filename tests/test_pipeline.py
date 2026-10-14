"""End-to-end test: real MCP servers over stdio, rules mode, temp database."""
import asyncio

from malariapulse import store
from malariapulse.pipeline import run_pipeline


def test_pipeline_over_mcp(tmp_path, monkeypatch):
    monkeypatch.setattr("malariapulse.store.DB_PATH", tmp_path / "t.db")
    out = asyncio.run(run_pipeline("rules", save=True))

    flagged = {p["zone"] for p in out["proposals"]}
    assert {"Lakeview", "Riverbend"} <= flagged
    used = {c["tool"] for c in out["tool_calls"]}
    # every agent really went through MCP tools
    assert {"assess_outbreak_risk", "compute_resupply_needs", "draft_advisory"} <= used

    pending = store.list_proposals("pending")
    assert len(pending) == len(out["proposals"])
    store.record_decision(pending[0]["id"], "approved", "tester", "ok", "final text")
    assert store.list_proposals("approved")[0]["reviewer"] == "tester"


def test_human_must_choose_valid_status(tmp_path, monkeypatch):
    import pytest
    monkeypatch.setattr("malariapulse.store.DB_PATH", tmp_path / "t2.db")
    with pytest.raises(ValueError):
        store.record_decision(1, "auto-sent", "x")
