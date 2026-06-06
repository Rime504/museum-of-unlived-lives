# Museum front door — gr.Blocks + custom FastAPI routes (HF Spaces compatible).

from __future__ import annotations

import asyncio.base_events as _base_events
import base64
import os
from pathlib import Path
from typing import Any


def _patch_asyncio_event_loop_del() -> None:
    """Suppress Gradio 6 HF Spaces log noise: BaseEventLoop.__del__ fd -1."""
    original_del = getattr(_base_events.BaseEventLoop, "__del__", None)
    if original_del is None or getattr(original_del, "_museum_patched", False):
        return

    def _patched_del(self: _base_events.BaseEventLoop) -> None:
        try:
            original_del(self)
        except ValueError as exc:
            if "Invalid file descriptor" not in str(exc):
                raise

    _patched_del._museum_patched = True  # type: ignore[attr-defined]
    _base_events.BaseEventLoop.__del__ = _patched_del  # type: ignore[method-assign]


_patch_asyncio_event_loop_del()

# HF Spaces enables SSR by default in Gradio 6; disable before gradio import.
os.environ.setdefault("GRADIO_SSR_MODE", "false")

import gradio as gr
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from museum.card import render_card
from museum.export import export_card_png
from museum.model import kick_warmup, preload_curator_gpu
from museum.prompts import format_counterfactual
from museum.schema import create_exhibit

ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT / "frontend"
INDEX_HTML = FRONTEND_DIR / "index.html"

# Custom FastAPI shell: static files + index.html at /. Passed to Blocks.launch(_app=...).
custom_app = gr.Server()
custom_app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@custom_app.get("/")
def index() -> HTMLResponse:
    return HTMLResponse(INDEX_HTML.read_text(encoding="utf-8"))


def _png_data_uri(path: Path) -> str:
    raw = Path(path).read_bytes()
    return "data:image/png;base64," + base64.b64encode(raw).decode("ascii")


def open_room(user_line: str) -> dict[str, Any]:
    """Turn one counterfactual line into a museum exhibit payload for the frontend."""
    text = (user_line or "").strip()
    if not text:
        return {
            "ok": False,
            "error": "Share a path you did not take — the words that follow “What if”.",
        }

    try:
        exhibit = create_exhibit(text)
        card_html = render_card(exhibit)
        png_path = export_card_png(exhibit)
        return {
            "ok": True,
            "title": exhibit.exhibit_title,
            "counterfactual": format_counterfactual(text),
            "mood": exhibit.style.mood,
            "card_html": card_html,
            "png": _png_data_uri(png_path),
        }
    except Exception as e:  # noqa: BLE001
        return {
            "ok": False,
            "error": f"The museum could not open this room. ({type(e).__name__}: {e})",
        }


def preload_curator() -> dict[str, Any]:
    """Load model into GPU memory — called from the frontend when the page opens."""
    try:
        preload_curator_gpu()
        return {"ok": True}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}


# HF Spaces expects `demo` to be gr.Blocks (not gr.Server) for its file watcher.
with gr.Blocks(title="Museum of Unlived Lives") as demo:
    gr.api(open_room, api_name="open_room")
    gr.api(preload_curator, api_name="preload_curator")

demo.queue(max_size=4)

# HF Spaces imports app.py directly — custom_app.on_event("startup") never fires.
# Kick weight download as soon as the module loads.
kick_warmup()


if __name__ == "__main__":
    demo.launch(
        _app=custom_app,
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", "7860")),
        show_error=True,
        ssr_mode=False,
    )
