# Parse + validate what MiniCPM returns. One retry if JSON is broken.

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

from museum.model import ask_curator
from museum.prompts import format_counterfactual
from museum.spec import SHAPE_KEYS, resolve_shape_key


class ExhibitStyle(BaseModel):
    mood: str
    palette: list[str] = Field(min_length=3, max_length=3)
    shape: str

    @field_validator("shape")
    @classmethod
    def canonical_shape(cls, v: str) -> str:
        return resolve_shape_key(v)

    @field_validator("palette")
    @classmethod
    def hex_colors(cls, v: list[str]) -> list[str]:
        out = []
        for color in v:
            c = color.strip()
            if not re.fullmatch(r"#[0-9A-Fa-f]{6}", c):
                c = "#6B5B95"
            out.append(c)
        return out


class Exhibit(BaseModel):
    exhibit_title: str
    narrative: str
    artifact: str
    style: ExhibitStyle


def _strip_markdown_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    return t.strip()


def _strip_thinking_blocks(text: str) -> str:
    t = text.strip()
    for open_name, close_name in (
        ("think", "think"),
        ("redacted_thinking", "redacted_thinking"),
    ):
        t = re.sub(
            rf"<{open_name}[^>]*>.*?</{close_name}>",
            "",
            t,
            flags=re.DOTALL | re.IGNORECASE,
        )
    return t.strip()


def _normalize_json_text(text: str) -> str:
    """MiniCPM often emits literal backslash-quotes instead of valid JSON."""
    t = _strip_thinking_blocks(_strip_markdown_fences(text)).strip()
    if not t:
        return t
    if '\\"' in t or "\\'" in t:
        t = t.replace('\\"', '"').replace("\\'", "'")
    return t


def _extract_json_object(text: str) -> dict[str, Any]:
    t = _normalize_json_text(text)
    if not t:
        raise json.JSONDecodeError("empty model output", t, 0)
    try:
        data = json.loads(t)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    start = t.find("{")
    if start == -1:
        raise json.JSONDecodeError("no JSON object in model output", t, 0)

    depth = 0
    for i in range(start, len(t)):
        ch = t[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(t[start : i + 1])
    raise json.JSONDecodeError("unbalanced JSON object", t, start)


def _parse_exhibit(raw: str) -> Exhibit:
    return Exhibit.model_validate(_extract_json_object(raw))


def create_exhibit(user_line: str) -> Exhibit:
    counterfactual = format_counterfactual(user_line)
    raw = ask_curator(counterfactual)
    try:
        return _parse_exhibit(raw)
    except Exception as first_err:
        fix_prompt = (
            "Return corrected JSON only. Same keys: exhibit_title, narrative, "
            f"artifact, style (mood, palette, shape — exactly one of: "
            f"{', '.join(SHAPE_KEYS)}). No markdown.\n{raw[:2000]}"
        )
        try:
            repaired = ask_curator(counterfactual, repair=fix_prompt)
            return _parse_exhibit(repaired)
        except Exception as second_err:
            preview = (raw or "").strip()[:240].replace("\n", " ")
            raise RuntimeError(
                f"Could not parse exhibit JSON. First: {first_err}; retry: {second_err}. "
                f"Raw preview: {preview!r}"
            ) from second_err
