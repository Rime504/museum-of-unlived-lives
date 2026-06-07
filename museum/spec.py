# JSON shape the model must return, plus word → SVG renderer lookup.

from __future__ import annotations

DEFAULT_SHAPE_KEY = "concentric"

SHAPE_KEYS: tuple[str, ...] = (
    "spiral",
    "fracture",
    "shards",
    "waves",
    "dots",
    "blob",
    "planes",
    "concentric",
)

SHAPE_KEYWORDS: dict[str, str] = {
    "fracture": "fracture",
    "crack": "fracture",
    "fissure": "fracture",
    "break": "fracture",
    "concentric": "concentric",
    "void": "concentric",
    "circle": "concentric",
    "ring": "concentric",
    "spiral": "spiral",
    "coil": "spiral",
    "shard": "shards",
    "angular": "shards",
    "fragment": "shards",
    "plane": "planes",
    "intersect": "planes",
    "grid": "planes",
    "wave": "waves",
    "layer": "waves",
    "dot": "dots",
    "scatter": "dots",
    "point": "dots",
    "blob": "blob",
    "organic": "blob",
    "amorphous": "blob",
}

EXHIBIT_JSON_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "exhibit_title": {"type": "string"},
        "narrative": {"type": "string"},
        "artifact": {"type": "string"},
        "style": {
            "type": "object",
            "properties": {
                "mood": {"type": "string"},
                "palette": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 3,
                    "maxItems": 3,
                },
                "shape": {"type": "string", "enum": list(SHAPE_KEYS)},
            },
            "required": ["mood", "palette", "shape"],
        },
    },
    "required": ["exhibit_title", "narrative", "artifact", "style"],
}


def resolve_shape_key(shape_text: str) -> str:
    key = (shape_text or "").strip().lower()
    if key in SHAPE_KEYS:
        return key
    for word, renderer in SHAPE_KEYWORDS.items():
        if word in key:
            return renderer
    return DEFAULT_SHAPE_KEY
