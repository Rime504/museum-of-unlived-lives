# GBNF grammar from exhibit JSON schema — forces valid JSON from MiniCPM.

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

EXHIBIT_JSON_SCHEMA: dict[str, Any] = {
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
                },
                "shape": {"type": "string"},
            },
            "required": ["mood", "palette", "shape"],
            "additionalProperties": False,
        },
    },
    "required": ["exhibit_title", "narrative", "artifact", "style"],
    "additionalProperties": False,
}


@lru_cache(maxsize=1)
def get_exhibit_grammar():
    from llama_cpp import LlamaGrammar

    return LlamaGrammar.from_json_schema(
        json.dumps(EXHIBIT_JSON_SCHEMA),
        verbose=False,
    )
