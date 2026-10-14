"""SQLite store for agent proposals and human review decisions (the audit trail)."""
import json
import sqlite3
from datetime import datetime, timezone

from .config import DB_PATH


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            zone TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            payload TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            reviewer TEXT,
            reviewed_at TEXT,
            reviewer_note TEXT,
            final_text TEXT
        )"""
    )
    return conn


def save_proposals(proposals: list[dict]) -> list[int]:
    ids = []
    with _conn() as conn:
        for p in proposals:
            cur = conn.execute(
                "INSERT INTO proposals (created_at, zone, risk_level, payload) VALUES (?, ?, ?, ?)",
                (datetime.now(timezone.utc).isoformat(), p["zone"], p["risk"]["risk_level"], json.dumps(p)),
            )
            ids.append(cur.lastrowid)
    return ids


def list_proposals(status: str | None = None) -> list[dict]:
    q, args = "SELECT * FROM proposals", ()
    if status:
        q, args = q + " WHERE status = ?", (status,)
    with _conn() as conn:
        rows = conn.execute(q + " ORDER BY id DESC", args).fetchall()
    return [{**dict(r), "payload": json.loads(r["payload"])} for r in rows]


def record_decision(proposal_id: int, status: str, reviewer: str, note: str = "", final_text: str = "") -> None:
    if status not in ("approved", "rejected"):
        raise ValueError("status must be 'approved' or 'rejected'")
    with _conn() as conn:
        conn.execute(
            "UPDATE proposals SET status=?, reviewer=?, reviewed_at=?, reviewer_note=?, final_text=? WHERE id=?",
            (status, reviewer, datetime.now(timezone.utc).isoformat(), note, final_text, proposal_id),
        )
