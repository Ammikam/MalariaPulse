"""Paths and settings shared across the project."""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("MALARIAPULSE_DATA", REPO_ROOT / "data"))
DB_PATH = Path(os.environ.get("MALARIAPULSE_DB", DATA_DIR / "malariapulse.db"))

# Risk thresholds used by the forecast and the supply agent
HIGH_RISK = 0.55
MODERATE_RISK = 0.30
