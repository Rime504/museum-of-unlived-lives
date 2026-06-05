# SVG art at the top of each card. Story palette tints the shape; shell stays dark.

from __future__ import annotations

import hashlib
import math
import random
from typing import TYPE_CHECKING

from museum.spec import DEFAULT_SHAPE_KEY, resolve_shape_key

if TYPE_CHECKING:
    from museum.schema import Exhibit

SIZE = 220


def _seed(exhibit: Exhibit) -> int:
    key = f"{exhibit.exhibit_title}|{exhibit.style.shape}|{','.join(exhibit.style.palette)}"
    return int(hashlib.sha256(key.encode()).hexdigest()[:12], 16)


def _svg_header(size: int, bg: str, opacity: str = "0.15") -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'width="{size}" height="{size}" class="museum-shape-svg">',
        f'<rect width="{size}" height="{size}" fill="{bg}" opacity="{opacity}"/>',
    ]


def _render_fracture(palette: list[str], rng: random.Random, size: int) -> str:
    c0, c1, c2 = palette
    parts = _svg_header(size, c2)
    cx, cy = size // 2, size // 2
    angle = rng.uniform(-0.8, 0.8)
    length = size * 0.7
    x2 = cx + length * math.cos(angle)
    y2 = cy + length * math.sin(angle)
    parts.append(
        f'<line x1="{cx - 20}" y1="{cy + 10}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{c0}" stroke-width="2" opacity="0.85"/>'
    )
    for i in range(4):
        bx = cx + (x2 - cx) * (0.3 + i * 0.15)
        by = cy + (y2 - cy) * (0.3 + i * 0.15)
        parts.append(
            f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{bx + rng.randint(-30, 30):.1f}" '
            f'y2="{by + rng.randint(-25, 25):.1f}" stroke="{c1}" stroke-width="1" opacity="0.6"/>'
        )
    parts.append("</svg>")
    return "".join(parts)


def _render_concentric(palette: list[str], rng: random.Random, size: int) -> str:
    c0, c1, c2 = palette
    parts = _svg_header(size, c2)
    cx = size / 2 + rng.randint(-14, 14)
    cy = size / 2 + rng.randint(-14, 14)
    for i, r in enumerate(range(int(size * 0.42), 12, -14)):
        fill = [c0, c1, c2][i % 3]
        op = 0.2 + i * 0.07
        parts.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}" fill-opacity="{op:.2f}"/>'
        )
    parts.append("</svg>")
    return "".join(parts)


def _render_spiral(palette: list[str], rng: random.Random, size: int) -> str:
    c0, c1, _c2 = palette
    parts = _svg_header(size, _c2)
    cx = size / 2 + rng.randint(-10, 10)
    cy = size / 2 + rng.randint(-10, 10)
    pts = []
    for t in range(0, 540, 6):
        ang = math.radians(t)
        r = 3 + t * 0.14
        pts.append(f"{cx + r * math.cos(ang):.1f},{cy + r * math.sin(ang):.1f}")
    parts.append(
        f'<polyline points="{" ".join(pts)}" fill="none" stroke="{c0}" '
        f'stroke-width="2" opacity="0.75"/>'
    )
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="5" fill="{c1}"/>')
    parts.append("</svg>")
    return "".join(parts)


def _render_shards(palette: list[str], rng: random.Random, size: int) -> str:
    c0, c1, c2 = palette
    parts = _svg_header(size, c2)
    for i in range(12):
        x1, y1 = rng.randint(0, size), rng.randint(0, size)
        x2, y2 = x1 + rng.randint(25, 70), y1 + rng.randint(-35, 35)
        x3, y3 = x2 + rng.randint(-15, 25), y2 + rng.randint(35, 75)
        fill = [c0, c1, c2][i % 3]
        parts.append(
            f'<polygon points="{x1},{y1} {x2},{y2} {x3},{y3}" '
            f'fill="{fill}" fill-opacity="0.5"/>'
        )
    parts.append("</svg>")
    return "".join(parts)


def _render_planes(palette: list[str], rng: random.Random, size: int) -> str:
    c0, c1, c2 = palette
    parts = _svg_header(size, c2)
    for i, (fill, xoff) in enumerate([(c0, 0), (c1, 30), (c0, 60)]):
        parts.append(
            f'<rect x="{20 + xoff}" y="{40 + i * 35}" width="{size - 80}" height="4" '
            f'fill="{fill}" opacity="0.7" transform="rotate({-15 + i * 12} {size/2} {size/2})"/>'
        )
    parts.append(
        f'<line x1="30" y1="{size - 40}" x2="{size - 30}" y2="50" '
        f'stroke="{c1}" stroke-width="1.5" opacity="0.55"/>'
    )
    parts.append("</svg>")
    return "".join(parts)


def _render_waves(palette: list[str], rng: random.Random, size: int) -> str:
    c0, c1, c2 = palette
    offset = rng.randint(-12, 12)
    parts = _svg_header(size, c2)
    for i, (fill, y0) in enumerate([(c0, 50), (c1, 95), (c0, 140)]):
        y0 += offset + i * 4
        d = f"M0,{y0} Q{size//4},{y0 - 22} {size//2},{y0} T{size},{y0} V{size} H0 Z"
        parts.append(f'<path d="{d}" fill="{fill}" fill-opacity="0.4"/>')
    parts.append("</svg>")
    return "".join(parts)


def _render_dots(palette: list[str], rng: random.Random, size: int) -> str:
    c0, c1, c2 = palette
    parts = _svg_header(size, c2)
    for _ in range(36):
        x, y = rng.randint(12, size - 12), rng.randint(12, size - 12)
        r = rng.randint(2, 8)
        fill = [c0, c1, c2][rng.randint(0, 2)]
        parts.append(
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" fill-opacity="0.65"/>'
        )
    parts.append("</svg>")
    return "".join(parts)


def _render_blob(palette: list[str], rng: random.Random, size: int) -> str:
    c0, c1, c2 = palette
    cx, cy = size / 2, size / 2
    parts = _svg_header(size, c2)
    for fill, scale in [(c1, 1.0), (c0, 0.72), (c1, 0.48)]:
        pts = []
        for i in range(9):
            ang = (2 * math.pi * i) / 9
            wobble = 38 * scale + rng.randint(-6, 6)
            pts.append(f"{cx + wobble * math.cos(ang):.1f},{cy + wobble * math.sin(ang):.1f}")
        parts.append(f'<polygon points="{" ".join(pts)}" fill="{fill}" fill-opacity="0.45"/>')
    parts.append("</svg>")
    return "".join(parts)


_RENDERERS = {
    "fracture": _render_fracture,
    "concentric": _render_concentric,
    "spiral": _render_spiral,
    "shards": _render_shards,
    "planes": _render_planes,
    "waves": _render_waves,
    "dots": _render_dots,
    "blob": _render_blob,
}


def draw_shape(exhibit: Exhibit, size: int = SIZE) -> str:
    key = resolve_shape_key(exhibit.style.shape)
    renderer = _RENDERERS.get(key, _RENDERERS[DEFAULT_SHAPE_KEY])
    rng = random.Random(_seed(exhibit))
    return renderer(list(exhibit.style.palette), rng, size)
