from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from museum.schema import Exhibit, ExhibitStyle
from museum.shapes import draw_shape
from museum.spec import resolve_shape_key

SHAPE_TEXTS = [
    "a single fracture line",
    "concentric voids",
    "intersecting planes",
    "a gentle spiral",
    "scattered points of light",
    "layered waves",
    "an organic blob",
    "something unknown and abstract",
]


def _exhibit(title: str, shape: str, palette: list[str]) -> Exhibit:
    return Exhibit(
        exhibit_title=title,
        narrative="A quiet life unfolded.",
        artifact="A folded letter.",
        style=ExhibitStyle(mood="severe, luminous", palette=palette, shape=shape),
    )


def main() -> int:
    pal_a = ["#1a2a3a", "#6B5B95", "#D8D3E0"]
    pal_b = ["#2d1b2e", "#8b4a6b", "#e8d5e0"]
    ok = True

    for shape_text in SHAPE_TEXTS:
        ex = _exhibit("Test Room", shape_text, pal_a)
        svg = draw_shape(ex)
        key = resolve_shape_key(shape_text)
        if not svg or "<svg" not in svg:
            print(f"FAIL empty svg for {shape_text!r} (key={key})")
            ok = False
        else:
            print(f"OK  {shape_text!r} -> {key} ({len(svg)} chars)")

    ex = _exhibit("Same", "concentric voids", pal_a)
    assert draw_shape(ex) == draw_shape(ex), "determinism failed"
    ex2 = _exhibit("Different Title Seed", "concentric voids", pal_a)
    assert draw_shape(ex) != draw_shape(ex2), "title seed should change svg"
    ex3 = _exhibit("Same", "concentric voids", pal_b)
    assert draw_shape(ex) != draw_shape(ex3), "palette should change svg"
    print("OK  determinism + uniqueness")

    print("GATE PASS" if ok else "GATE FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
