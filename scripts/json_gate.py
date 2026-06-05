# Smoke test: 20 counterfactuals, need 90%+ valid JSON from MiniCPM.

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from museum.schema import create_exhibit

SAMPLES = [
    "I had stayed in the city that winter",
    "I never picked up the phone",
    "I had chosen the other door",
    "I almost moved to Japan at nineteen",
    "I said no to the job in Berlin",
    "I never learned to swim",
    "I had married the first person who asked",
    "I stayed in the town where I was born",
    "I never sent the letter",
    "I took the safer path every time",
    "I had trusted my instinct that morning",
    "I never confronted my father",
    "I had become a musician instead",
    "I walked away from the argument",
    "I never left my hometown",
    "I had said yes when they offered",
    "I kept the secret until it hardened",
    "I chose comfort over curiosity",
    "I never boarded that train",
    "I had forgiven them sooner",
]


def main() -> int:
    ok = 0
    total = len(SAMPLES)
    for sample in SAMPLES:
        try:
            e = create_exhibit(sample)
            assert e.exhibit_title and e.narrative and e.artifact
            assert len(e.style.palette) == 3
            ok += 1
            print(f"OK  {sample[:40]}... -> {e.exhibit_title[:30]}")
        except Exception as exc:
            print(f"FAIL {sample[:40]}... -> {exc}")

    pct = 100 * ok / total
    print(f"\n{ok}/{total} valid ({pct:.0f}%)")
    if pct >= 90:
        print("GATE PASS")
        return 0
    print("GATE FAIL — need ≥90%")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
