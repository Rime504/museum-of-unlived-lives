# One JSON line per generation → trace.jsonl

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TRACE_FILE = Path(__file__).resolve().parent.parent / "trace.jsonl"
TRACE_DATASET = os.environ.get("MUSEUM_TRACE_DATASET", "divmodelhq/museum-unlived-lives-trace")


def log_generation(user_line: str, exhibit: dict[str, Any]) -> None:
    row = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "input": user_line,
        "counterfactual": f"What if {user_line.strip()}",
        "output": exhibit,
    }
    line = json.dumps(row, ensure_ascii=False)
    if "api_key" in line.lower():
        raise ValueError("refusing to log secrets")
    with TRACE_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def trace_count() -> int:
    if not TRACE_FILE.is_file():
        return 0
    return sum(1 for _ in TRACE_FILE.open(encoding="utf-8"))
