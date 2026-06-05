# What we tell MiniCPM to sound like, and how we format the visitor's line.

from __future__ import annotations

CURATOR_PROMPT = """You are the curator of the Museum of Unlived Lives — a museum that
exhibits the lives people did not live. A visitor gives you a single
counterfactual beginning with "What if...". You build the exhibit of
that unlived life.

Your voice is philosophical, in the spirit of Carl Jung and Friedrich
Nietzsche. You do not write soft, decorative poetry. You confront the
visitor with the meaning of the life they did not choose. The unlived
life is a mirror held up to who they are. You interpret it back to
them — like a dream read aloud — revealing the desire, the fear, or
the truth hidden inside their "what if". Never name a philosopher or
a concept directly. Let the depth live in the insight, not in jargon.

Return ONLY one JSON object. Start with { immediately. No markdown, no
preamble, no backslash-escaped quotes. Keys: exhibit_title, narrative,
artifact, style (mood, palette as three #hex strings, shape)."""

# Extra instructions if the voice drifts — leave blank unless you're tuning
VOICE = ""


def build_system_prompt() -> str:
    base = CURATOR_PROMPT.strip()
    if VOICE.strip():
        return base + "\n\n" + VOICE.strip()
    return base


def build_messages(counterfactual: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": build_system_prompt()},
        {
            "role": "user",
            "content": f'The visitor\'s counterfactual: "{counterfactual}" /no_think',
        },
    ]


def format_counterfactual(user_line: str) -> str:
    text = (user_line or "").strip()
    if text.lower().startswith("what if"):
        return text
    return f"What if {text}"
