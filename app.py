# Museum front door — gr.Server custom UI + /open_room API.

from __future__ import annotations

import base64
import os
import threading
from pathlib import Path
from typing import Any

# HF Spaces enables SSR by default in Gradio 6; disable before gradio import.
os.environ.setdefault("GRADIO_SSR_MODE", "false")
os.environ.setdefault("GRADIO_HOT_RELOAD", "false")

import gradio as gr
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from museum.card import render_card
from museum.export import export_card_png
from museum.model import preload_model
from museum.prompts import format_counterfactual
from museum.schema import create_exhibit
from museum.trace import log_generation

ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT / "frontend"
INDEX_HTML = FRONTEND_DIR / "index.html"

# HF Spaces looks for a module-level object named `demo`.
demo = gr.Server()
demo.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


def _png_data_uri(path: Path) -> str:
    raw = Path(path).read_bytes()
    return "data:image/png;base64," + base64.b64encode(raw).decode("ascii")


@demo.api(name="open_room")
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
        log_generation(text, exhibit.model_dump())
        return {
            "ok": True,
            "title": exhibit.exhibit_title,
            "counterfactual": format_counterfactual(text),
            "mood": exhibit.style.mood,
            "card_html": card_html,
            "png": _png_data_uri(png_path),
        }
    except Exception as e:  # noqa: BLE001 — surface a friendly message to the gallery wall
        return {
            "ok": False,
            "error": f"The museum could not open this room. ({type(e).__name__}: {e})",
        }


@demo.get("/")
def index() -> HTMLResponse:
    return HTMLResponse(INDEX_HTML.read_text(encoding="utf-8"))


if os.environ.get("MUSEUM_WARMUP", "false").lower() in ("1", "true", "yes"):
    threading.Thread(target=preload_model, daemon=True).start()


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", "7860")),
        show_error=True,
        ssr_mode=False,
    )
