# HTML for one exhibit card. Styles live in frontend/styles.css (.museum-card*).

from __future__ import annotations

import html
from typing import TYPE_CHECKING

from museum.shapes import draw_shape

if TYPE_CHECKING:
    from museum.schema import Exhibit


def render_card(exhibit: Exhibit) -> str:
    shape_svg = draw_shape(exhibit)
    title = html.escape(exhibit.exhibit_title)
    narrative = html.escape(exhibit.narrative)
    artifact = html.escape(exhibit.artifact)
    mood = html.escape(exhibit.style.mood.upper())

    colors = exhibit.style.palette
    palette_vars = (
        f"--shape-0: {colors[0]}; --shape-1: {colors[1]}; --shape-2: {colors[2]};"
    )

    return f"""<article class="museum-card" style="{palette_vars}">
  <div class="museum-card__shape-wrap">
    <div class="museum-card__shape">{shape_svg}</div>
  </div>
  <p class="museum-card__mood">{mood}</p>
  <h1 class="museum-card__title">{title}</h1>
  <p class="museum-card__narrative">{narrative}</p>
  <footer class="museum-card__placard">
    <span class="museum-card__placard-label">On display</span>
    <p class="museum-card__artifact">{artifact}</p>
  </footer>
</article>"""
