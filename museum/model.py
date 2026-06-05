# MiniCPM on disk (or downloaded once) → exhibit JSON via llama.cpp.

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from museum.grammar import get_exhibit_grammar
from museum.prompts import build_messages

ROOT = Path(__file__).resolve().parent.parent
WEIGHTS_FILE = "minicpm-8b-q4_k_m.gguf"
WEIGHTS_PATH = ROOT / WEIGHTS_FILE
HF_REPO = "openbmb/MiniCPM4.1-8B-GGUF"
HF_FILENAME = "MiniCPM4.1-8B-Q4_K_M.gguf"

_minicpm: Any = None

# llama-cpp-python 0.3.23 on HF does not accept chat_template_kwargs on completion calls.
_STOP_SEQUENCES = ["<|im_end|>", "<|im_start|>", "<user>", "<assistant>", "</s>"]


def get_weights_path() -> Path:
    if WEIGHTS_PATH.is_file():
        return WEIGHTS_PATH

    alt = ROOT / HF_FILENAME
    if alt.is_file():
        return alt

    print(f"Pulling {HF_FILENAME} from {HF_REPO} (~4.97 GB)...")
    from huggingface_hub import hf_hub_download

    cached = hf_hub_download(repo_id=HF_REPO, filename=HF_FILENAME)
    shutil.copy2(cached, WEIGHTS_PATH)
    print(f"Saved to {WEIGHTS_PATH}")
    return WEIGHTS_PATH


def _init_minicpm() -> Any:
    global _minicpm
    if _minicpm is not None:
        return _minicpm

    from llama_cpp import Llama

    path = get_weights_path()
    _minicpm = Llama(
        model_path=str(path),
        n_gpu_layers=int(os.environ.get("MUSEUM_N_GPU_LAYERS", "-1")),
        n_ctx=int(os.environ.get("MUSEUM_N_CTX", "4096")),
        n_threads=int(os.environ.get("MUSEUM_N_THREADS", "4")),
        verbose=False,
    )
    return _minicpm


def _messages_to_prompt(messages: list[dict[str, str]]) -> str:
    """MiniCPM4 ChatML-style prompt — avoids chat_template_kwargs on completion."""
    chunks: list[str] = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            chunks.append(f"<|im_start|>system\n{content}\n")
        elif role == "user":
            chunks.append(f"<|im_start|>user\n{content}\n")
        elif role == "assistant":
            chunks.append(f"<|im_start|>assistant\n{content}\n")
    chunks.append("<|im_start|>assistant\n")
    return "".join(chunks)


def _message_text(message: dict[str, Any]) -> str:
    content = (message.get("content") or "").strip()
    reasoning = (message.get("reasoning_content") or "").strip()
    if content and reasoning:
        return content if content.startswith("{") else reasoning
    return content or reasoning


def _raw_complete(
    llm: Any,
    messages: list[dict[str, str]],
    *,
    max_tokens: int,
    temperature: float,
    use_grammar: bool = True,
) -> str:
    prompt = _messages_to_prompt(messages)
    kwargs: dict[str, Any] = {
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stop": _STOP_SEQUENCES,
        "echo": False,
    }
    if use_grammar:
        try:
            kwargs["grammar"] = get_exhibit_grammar()
        except Exception as exc:
            print(f"Grammar sampling unavailable, falling back: {exc}")
    out = llm(prompt, **kwargs)
    return (out["choices"][0].get("text") or "").strip()


def ask_curator(
    counterfactual: str,
    *,
    repair: str | None = None,
    max_tokens: int = 800,
) -> str:
    is_repair = repair is not None
    if is_repair:
        messages = [
            {"role": "system", "content": "Return corrected JSON only. No markdown."},
            {"role": "user", "content": f"{repair} /no_think"},
        ]
    else:
        messages = build_messages(counterfactual)

    llm = _init_minicpm()
    temperature = 0.4

    # Prefer raw string completion — stable on HF; no hidden OpenAI-style kwargs.
    text = _raw_complete(
        llm,
        messages,
        max_tokens=max_tokens,
        temperature=temperature,
        use_grammar=not is_repair,
    )

    if not text:
        try:
            out = llm.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            text = _message_text(out["choices"][0]["message"])
        except TypeError as exc:
            raise RuntimeError(f"Model completion failed: {exc}") from exc

    if not text:
        raise RuntimeError("Model returned empty text — try again or check /no_think")
    return text


def preload_model() -> None:
    try:
        _init_minicpm()
    except Exception as exc:
        print(f"Preload skipped: {exc}")


if __name__ == "__main__":
    import sys

    line = sys.argv[1] if len(sys.argv) > 1 else "What if I had said yes"
    print(ask_curator(line))
