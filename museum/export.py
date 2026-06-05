# Turn an exhibit into a PNG someone can download or post.

from __future__ import annotations

import io
import math
import textwrap
from pathlib import Path
from typing import TYPE_CHECKING

from museum.spec import resolve_shape_key

if TYPE_CHECKING:
    from museum.schema import Exhibit

OUT_DIR = Path(__file__).resolve().parent.parent / "exports"
CARD_W, CARD_H = 900, 1200

# Placard frame — fixed. Story colors only hit the shape, not these.
FRAME_BG = "#14121A"
FRAME_LINE = "#2A2733"
FRAME_TEXT = "#D8D3E0"
FRAME_ACCENT = "#6B5B95"


def _font(size: int):
    from PIL import ImageFont

    for path in (
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"),
    ):
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _shape_bitmap_fallback(exhibit: Exhibit, size: int = 260):
    from PIL import Image, ImageDraw

    colors = exhibit.style.palette
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    kind = resolve_shape_key(exhibit.style.shape)

    if kind == "fracture":
        draw.line((cx - 40, cy + 15, cx + 90, cy - 30), fill=colors[0], width=3)
        draw.line((cx + 20, cy - 5, cx + 50, cy + 25), fill=colors[1], width=2)
    elif kind == "concentric":
        for i, r in enumerate(range(100, 15, -15)):
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=colors[i % 3], width=2)
    elif kind == "spiral":
        for t in range(0, 300, 8):
            rad = math.radians(t)
            r = 8 + t * 0.2
            x, y = cx + r * math.cos(rad), cy + r * math.sin(rad)
            draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=colors[0])
    else:
        draw.ellipse((40, 40, size - 40, size - 40), outline=colors[1], width=2)
        draw.line((30, cy, size - 30, cy), fill=colors[0], width=2)

    return img


def _shape_bitmap(exhibit: Exhibit, size: int = 260):
    try:
        import cairosvg
        from museum.shapes import draw_shape
        from PIL import Image

        png = cairosvg.svg2png(bytestring=draw_shape(exhibit, size=size).encode())
        return Image.open(io.BytesIO(png)).convert("RGBA")
    except (ImportError, OSError):
        return _shape_bitmap_fallback(exhibit, size)


def export_card_png(exhibit: Exhibit, out_path: Path | None = None) -> Path:
    from PIL import Image, ImageDraw

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in exhibit.exhibit_title[:40])
    out_path = out_path or OUT_DIR / f"{safe}.png"

    img = Image.new("RGB", (CARD_W, CARD_H), FRAME_BG)
    draw = ImageDraw.Draw(img)

    margin = 48
    draw.rectangle(
        (margin, margin, CARD_W - margin, CARD_H - margin),
        outline=FRAME_LINE,
        width=2,
    )

    shape_img = _shape_bitmap(exhibit, 240)
    img.paste(shape_img, (CARD_W // 2 - 120, margin + 24), shape_img)

    title_font = _font(40)
    body_font = _font(22)
    label_font = _font(14)
    mood_font = _font(16)

    y = margin + 280
    mood = exhibit.style.mood.upper()
    draw.text((margin + 24, y), mood, fill=FRAME_ACCENT, font=mood_font)
    y += 36

    draw.text((margin + 24, y), exhibit.exhibit_title, fill=FRAME_TEXT, font=title_font)
    y += 64

    for line in textwrap.wrap(exhibit.narrative, width=54):
        draw.text((margin + 24, y), line, fill=FRAME_TEXT, font=body_font)
        y += 30
    y += 28

    draw.line((margin + 24, y, margin + 28, y + 48), fill=FRAME_ACCENT, width=3)
    draw.text((margin + 40, y), "ON DISPLAY", fill=FRAME_ACCENT, font=label_font)
    y += 28
    for line in textwrap.wrap(exhibit.artifact, width=52):
        draw.text((margin + 40, y), line, fill=FRAME_TEXT, font=body_font)
        y += 28

    img.save(out_path, "PNG")
    return out_path
