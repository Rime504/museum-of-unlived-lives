# GBNF grammar from exhibit JSON schema — forces valid JSON from MiniCPM.

from __future__ import annotations

from functools import lru_cache

from museum.spec import EXHIBIT_JSON_SCHEMA


@lru_cache(maxsize=1)
def get_exhibit_grammar():
    import json

    from llama_cpp import LlamaGrammar

    return LlamaGrammar.from_json_schema(
        json.dumps(EXHIBIT_JSON_SCHEMA),
        verbose=False,
    )
