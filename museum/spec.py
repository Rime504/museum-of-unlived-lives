# Exhibit JSON schema + shape tokens for SVG renderers.

from __future__ import annotations

import hashlib

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

SHAPE_HINTS: dict[str, str] = {
    "spiral": "return, longing, going inward — a pull back to the same point",
    "fracture": "a clean break, rupture — the moment a path split in two",
    "shards": "shattered plans, regret — many sharp pieces of one choice",
    "waves": "time, memory, grief that returns — something rising and falling",
    "dots": "scattered possibilities, chance — a life of many small maybes",
    "blob": "formless desire, becoming — something soft and not yet shaped",
    "planes": "structure, career, duty — the architecture of a safe life",
    "concentric": "the void, stillness — a self circling its own center",
}

# Deep brief per shape — injected per request so copy matches server-assigned geometry.
SHAPE_BRIEFS: dict[str, dict[str, str]] = {
    "spiral": {
        "movement": "The psyche coils. What was left unfinished pulls the story back inward — not forward, not outward.",
        "mood": "orbital, recursive, drawn-back",
        "palette": "Deep base (ink, charcoal, midnight); one warm return-accent (amber, rust, ember); muted tertiary (violet, slate, moss).",
        "narrative": "Emphasize recurrence: almost choosing again, circling the same wound or door. Land on why they orbit instead of arrive.",
        "artifact": "Something repeated, withheld, or never delivered — a loop made object (unsent letter, unworn ring, path worn in carpet).",
        "avoid": "No clean rupture, no career grid, no random scatter.",
    },
    "fracture": {
        "movement": "One decisive split. Before and after are different worlds; the story lives at the hinge.",
        "mood": "severed, decisive, irreversible",
        "palette": "Dark ground split by a sharp contrast line — bone white, cold silver, or blood rust against black or deep blue.",
        "narrative": "Name the instant the path broke. Two selves, two futures; the insight is what each side cost.",
        "artifact": "Something broken along one line — cracked mirror, snapped key, torn ticket, two halves that no longer meet.",
        "avoid": "No soft drift, no gentle circles, no orderly career lattice.",
    },
    "shards": {
        "movement": "One choice splintered into many sharp pieces. Regret has angles.",
        "mood": "fragmented, sharp, unresolved",
        "palette": "Dark field with brittle accents — glass green, shard gold, bruise purple; colors feel cut, not blended.",
        "narrative": "Many consequences from one decision; pieces that cannot be reassembled. Land on what each fragment still cuts.",
        "artifact": "Broken into parts — ceramic shards, torn photographs, scattered beads, a watch with a cracked face.",
        "avoid": "No single clean break, no smooth waves, no empty void rings.",
    },
    "waves": {
        "movement": "Grief and memory rise, fall, return. Time is the subject — not a moment but a rhythm.",
        "mood": "tidal, returning, elegiac",
        "palette": "Layered blues, greys, sea-glass, wet stone; one pale crest color (foam white, pearl, mist).",
        "narrative": "Write what keeps coming back — anniversaries, seasons, the same feeling at different ages. Land on what the waves never wash away.",
        "artifact": "Something marked by time and tide — waterlogged book, faded ribbon, shells, a line on a doorframe.",
        "avoid": "No static void, no angular shatter, no rigid grids.",
    },
    "dots": {
        "movement": "Many small maybes, none chosen. Chance and contingency scatter across the life.",
        "mood": "open, contingent, uncommitted",
        "palette": "Dark ground with scattered points of color — star-field logic; three hues that never fully merge.",
        "narrative": "Emphasize paths not taken, near-misses, the weight of small forks. Land on how freedom became paralysis.",
        "artifact": "A collection of small things — dice, loose buttons, unmarked keys, a jar of coins from countries never visited.",
        "avoid": "No single rupture, no one dominant orbit, no fortress career.",
    },
    "blob": {
        "movement": "Becoming without form. Desire exists before it knows its shape.",
        "mood": "liminal, soft, unformed",
        "palette": "Organic gradients — dusk rose, clay, milk fog, deep peat; edges blur, nothing is hard-edged.",
        "narrative": "Write the life still forming — identity not yet claimed, want not yet named. Land on the fear or freedom of not being fixed.",
        "artifact": "Something soft, wet, or unfinished — clay without a mold, blurred photograph, unlabeled vial, wax not yet stamped.",
        "avoid": "No sharp breaks, no rigid structure, no hollow stillness.",
    },
    "planes": {
        "movement": "Order, duty, the life built on rules. Structure holds — and confines.",
        "mood": "structured, dutiful, restrained",
        "palette": "Architectural — slate, steel blue, parchment, brass; colors sit in clean layers, not chaos.",
        "narrative": "Emphasize the trade of safety for aliveness — the fortress, the credential, the role. Land on what the structure protected and what it buried.",
        "artifact": "Something institutional or ordered — badge, ledger, stacked files, pressed uniform, key to an office never left.",
        "avoid": "No formless drift, no scattered randomness, no void rings.",
    },
    "concentric": {
        "movement": "Stillness at the center. The self faces itself; the outer world thins.",
        "mood": "hollow, still, inward",
        "palette": "Ring logic — dark core, pale middle band, deep outer rim; muted, lunar, tomb-quiet.",
        "narrative": "Write withdrawal, silence, the life that narrows to one question. Land on what was avoided by staying at the center.",
        "artifact": "Something empty at the middle — hollow locket, ring with no stone, nest with no bird, mirror facing a blank wall.",
        "avoid": "No outward scatter, no career lattice, no sharp shatter.",
    },
}

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
            },
            "required": ["mood", "palette"],
        },
    },
    "required": ["exhibit_title", "narrative", "artifact", "style"],
}


def assign_shape_key(counterfactual: str) -> str:
    """Stable shape from counterfactual text — same prompt, same geometry."""
    key = (counterfactual or "").strip().lower()
    digest = hashlib.sha256(key.encode()).hexdigest()
    return SHAPE_KEYS[int(digest[:8], 16) % len(SHAPE_KEYS)]


def shape_hint(shape: str) -> str:
    return SHAPE_HINTS.get(shape, SHAPE_HINTS[DEFAULT_SHAPE_KEY])


def geometry_atlas() -> str:
    """Compact reference — all eight geometries the museum uses."""
    lines = ["EMOTIONAL GEOMETRY — the museum assigns one form per room (you do not choose):"]
    for key in SHAPE_KEYS:
        lines.append(f"  {key}: {SHAPE_HINTS[key]}")
    lines.append(
        "Read the assigned geometry in the visitor message. "
        "Mood, palette, narrative, and artifact must move like that form — "
        "never name the shape in JSON or prose."
    )
    return "\n".join(lines)


def assigned_geometry_block(shape: str) -> str:
    """Rich per-room brief so the model locks copy to server-assigned geometry."""
    key = shape if shape in SHAPE_BRIEFS else DEFAULT_SHAPE_KEY
    brief = SHAPE_BRIEFS[key]
    hint = SHAPE_HINTS[key]
    return f"""=== ASSIGNED GEOMETRY: {key} ===
Essence: {hint}

Movement: {brief["movement"]}
Mood register: {brief["mood"]}
Palette feel: {brief["palette"]}
Narrative focus: {brief["narrative"]}
Artifact tone: {brief["artifact"]}
Do NOT write like: {brief["avoid"]}

Before JSON: read the counterfactual through this geometry only.
- exhibit_title and narrative must feel like {key} in meaning, not in vocabulary
- style.mood must match the mood register above (two words, comma-separated)
- style.palette must match the palette feel above (three #hex)
- artifact must match the artifact tone above
Omit style.shape from JSON — the museum renders {key} automatically."""


def resolve_shape_key(shape_text: str) -> str:
    key = (shape_text or "").strip().lower()
    if key in SHAPE_KEYS:
        return key
    for word, renderer in SHAPE_KEYWORDS.items():
        if word in key:
            return renderer
    return DEFAULT_SHAPE_KEY
