# MiniCPM on disk (or downloaded once) → exhibit JSON via llama.cpp.
# On HF ZeroGPU Spaces, inference runs inside @spaces.GPU (GPU only when generating).

from __future__ import annotations

import os
import shutil
import threading
from pathlib import Path
from typing import Any, Callable, TypeVar

from museum.grammar import get_exhibit_grammar
from museum.prompts import build_messages

try:
    import spaces
except ImportError:
    spaces = None  # local dev / dedicated GPU Spaces

ROOT = Path(__file__).resolve().parent.parent
WEIGHTS_FILE = "minicpm-8b-q4_k_m.gguf"
WEIGHTS_PATH = ROOT / WEIGHTS_FILE
HF_REPO = "openbmb/MiniCPM4.1-8B-GGUF"
HF_FILENAME = "MiniCPM4.1-8B-Q4_K_M.gguf"

_minicpm: Any = None

# llama-cpp-python 0.3.23 on HF does not accept chat_template_kwargs on completion calls.
_STOP_SEQUENCES = ["<|im_end|>", "<|im_start|>", "<user>", "<assistant>", "</s>"]

_warmup_lock = threading.Lock()
_warmup_started = False
_weights_ready = threading.Event()
_init_lock = threading.Lock()

F = TypeVar("F", bound=Callable[..., Any])


def _gpu_wrap(fn: F) -> F:
    """Request a ZeroGPU slot on HF org Spaces; no-op elsewhere."""
    if spaces is None:
        return fn
    return spaces.GPU(duration=180)(fn)  # type: ignore[return-value]


def on_zero_gpu() -> bool:
    return spaces is not None and os.environ.get("SPACE_ID") is not None


def warmup_enabled() -> bool:
    return os.environ.get("MUSEUM_WARMUP", "true").lower() not in ("0", "false", "no")


def _preload_cuda_libs() -> None:
    """Expose pip-installed CUDA runtime to llama.cpp on ZeroGPU (no system libcudart)."""
    try:
        import ctypes
        import os

        import nvidia.cublas
        import nvidia.cuda_runtime
    except ImportError:
        return

    for module, lib_name in (
        (nvidia.cublas, "libcublas.so.12"),
        (nvidia.cuda_runtime, "libcudart.so.12"),
    ):
        lib_path = os.path.join(module.__path__[0], "lib", lib_name)
        if os.path.isfile(lib_path):
            ctypes.CDLL(lib_path, mode=ctypes.RTLD_GLOBAL)


def ensure_weights() -> Path:
    """Download GGUF weights if missing. Does not require GPU."""
    if WEIGHTS_PATH.is_file():
        return WEIGHTS_PATH

    alt = ROOT / HF_FILENAME
    if alt.is_file():
        return alt

    print(f"Pulling {HF_FILENAME} from {HF_REPO} (~4.97 GB)...", flush=True)
    from huggingface_hub import hf_hub_download

    cached = hf_hub_download(repo_id=HF_REPO, filename=HF_FILENAME)
    shutil.copy2(cached, WEIGHTS_PATH)
    print(f"Saved to {WEIGHTS_PATH}", flush=True)
    return WEIGHTS_PATH


def get_weights_path() -> Path:
    return ensure_weights()


def _init_minicpm() -> Any:
    global _minicpm
    if _minicpm is not None:
        return _minicpm

    with _init_lock:
        if _minicpm is not None:
            return _minicpm

        _preload_cuda_libs()
        from llama_cpp import Llama

        path = get_weights_path()
        print("Loading MiniCPM into memory...", flush=True)
        _minicpm = Llama(
            model_path=str(path),
            n_gpu_layers=int(os.environ.get("MUSEUM_N_GPU_LAYERS", "-1")),
            n_ctx=int(os.environ.get("MUSEUM_N_CTX", "4096")),
            n_threads=int(os.environ.get("MUSEUM_N_THREADS", "4")),
            verbose=False,
        )
        print("MiniCPM loaded.", flush=True)
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
    return _ask_curator_impl(counterfactual, repair=repair, max_tokens=max_tokens)


def wait_for_weights(timeout: float = 7200) -> None:
    """Wait for background weight download; no-op once weights are on disk."""
    if WEIGHTS_PATH.is_file() or (ROOT / HF_FILENAME).is_file():
        return
    if not warmup_enabled():
        return
    if not _weights_ready.wait(timeout=timeout):
        raise RuntimeError(
            "The curator is still downloading the model weights — try again shortly."
        )


@_gpu_wrap
def _ask_curator_impl(
    counterfactual: str,
    *,
    repair: str | None = None,
    max_tokens: int = 800,
) -> str:
    wait_for_weights()
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
    """Download weights at startup. ZeroGPU loads the model once on first /open_room."""
    try:
        print("Warmup: downloading weights if needed...", flush=True)
        ensure_weights()
        print("Warmup: weights ready on disk.", flush=True)
        if on_zero_gpu():
            print(
                "Warmup complete — MiniCPM loads once on first /open_room (ZeroGPU).",
                flush=True,
            )
        else:
            _init_minicpm()
            print("Warmup complete — curator is ready.", flush=True)
    except Exception as exc:
        print(f"Warmup failed (will retry on /open_room): {exc}", flush=True)
    finally:
        _weights_ready.set()


def kick_warmup() -> None:
    """Start background warmup once — safe to call from app import (HF Spaces)."""
    global _warmup_started

    if not warmup_enabled():
        _weights_ready.set()
        return

    with _warmup_lock:
        if _warmup_started:
            return
        _warmup_started = True

    threading.Thread(target=preload_model, daemon=True).start()


if __name__ == "__main__":
    import sys

    line = sys.argv[1] if len(sys.argv) > 1 else "What if I had said yes"
    print(ask_curator(line))
