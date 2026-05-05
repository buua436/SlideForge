from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Box:
    x: float
    y: float
    w: float
    h: float

    def inset(self, left: float = 0, top: float = 0, right: float | None = None, bottom: float | None = None) -> "Box":
        right = left if right is None else right
        bottom = top if bottom is None else bottom
        return Box(self.x + left, self.y + top, max(0, self.w - left - right), max(0, self.h - top - bottom))

    def split_cols(self, count: int, gutter: float = 0.0) -> list["Box"]:
        if count <= 0:
            return []
        col_w = (self.w - gutter * (count - 1)) / count
        return [Box(self.x + i * (col_w + gutter), self.y, col_w, self.h) for i in range(count)]

    def split_rows(self, count: int, gutter: float = 0.0) -> list["Box"]:
        if count <= 0:
            return []
        row_h = (self.h - gutter * (count - 1)) / count
        return [Box(self.x, self.y + i * (row_h + gutter), self.w, row_h) for i in range(count)]

    def top(self, height: float) -> "Box":
        return Box(self.x, self.y, self.w, min(height, self.h))

    def bottom(self, height: float) -> "Box":
        height = min(height, self.h)
        return Box(self.x, self.y + self.h - height, self.w, height)

    def remaining_below(self, top_height: float, gap: float = 0.0) -> "Box":
        y = self.y + top_height + gap
        return Box(self.x, y, self.w, max(0, self.y + self.h - y))


class PageBox(Box):
    @classmethod
    def from_theme(cls, theme: object) -> "PageBox":
        spacing = theme.spacing
        return cls(
            spacing.page_margin,
            spacing.page_y,
            theme.slide_width - spacing.page_margin * 2,
            theme.slide_height - spacing.page_y * 2,
        )


@dataclass(frozen=True)
class GridSpec:
    columns: int = 12
    rows: int = 6
    gap: float = 0.20


@dataclass(frozen=True)
class PageLayout:
    name: str = "standard"
    title_box: Box | None = None
    subtitle_box: Box | None = None
    content_box: Box | None = None
    footer_box: Box | None = None
    page_number_box: Box | None = None
    grid: GridSpec = field(default_factory=GridSpec)
    zones: dict[str, Box] = field(default_factory=dict)


def default_page_layout(name: str, theme: object) -> PageLayout:
    """Return a built-in page layout in inch units."""

    margin = theme.spacing.page_margin
    width = theme.slide_width
    height = theme.slide_height
    footer_y = theme.spacing.footer_y

    if name == "cover":
        return PageLayout(
            name="cover",
            title_box=Box(margin, 1.38, 7.2, 0.72),
            subtitle_box=Box(margin, 2.18, 7.2, 0.34),
            content_box=Box(margin, 3.05, width - margin * 2, 3.45),
            footer_box=Box(margin, footer_y, 5.2, 0.24),
            page_number_box=Box(width - margin - 0.8, footer_y + 0.05, 0.8, 0.18),
            grid=GridSpec(columns=12, rows=4, gap=theme.spacing.gutter),
        )

    if name == "section":
        return PageLayout(
            name="section",
            title_box=Box(3.05, 1.55, 8.0, 0.52),
            subtitle_box=Box(3.07, 2.13, 7.6, 0.30),
            content_box=Box(3.05, 2.92, 8.1, 2.65),
            footer_box=Box(margin, footer_y, 5.2, 0.24),
            page_number_box=Box(width - margin - 0.8, footer_y + 0.05, 0.8, 0.18),
            grid=GridSpec(columns=12, rows=3, gap=theme.spacing.gutter),
        )

    if name in {"blank", "full_bleed"}:
        return PageLayout(
            name=name,
            title_box=Box(margin, theme.spacing.title_top, 9.4, 0.42),
            subtitle_box=Box(margin, theme.spacing.title_top + 0.45, 9.4, 0.27),
            content_box=Box(0, 0, width, height),
            footer_box=Box(margin, footer_y, 5.2, 0.24),
            page_number_box=Box(width - margin - 0.8, footer_y + 0.05, 0.8, 0.18),
            grid=GridSpec(columns=12, rows=6, gap=theme.spacing.gutter),
        )

    if name in {"closing", "qa"}:
        return PageLayout(
            name=name,
            title_box=Box(margin, 1.35, width - margin * 2, 0.72),
            subtitle_box=Box(margin, 2.18, width - margin * 2, 0.32),
            content_box=Box(margin, 2.88, width - margin * 2, 3.50),
            footer_box=Box(margin, footer_y, 5.2, 0.24),
            page_number_box=Box(width - margin - 0.8, footer_y + 0.05, 0.8, 0.18),
            grid=GridSpec(columns=12, rows=4, gap=theme.spacing.gutter),
        )

    return PageLayout(
        name="standard",
        title_box=Box(margin, theme.spacing.title_top - 0.03, 9.2, 0.42),
        subtitle_box=Box(margin, theme.spacing.title_top + 0.45, 9.4, 0.27),
        content_box=Box(margin, theme.spacing.content_top, width - margin * 2, height - theme.spacing.content_top - 0.70),
        footer_box=Box(margin, footer_y, 5.2, 0.24),
        page_number_box=Box(width - margin - 0.8, footer_y + 0.05, 0.8, 0.18),
        grid=GridSpec(columns=12, rows=6, gap=theme.spacing.gutter),
    )


def layout_from_spec(spec: str | Mapping[str, Any] | None, theme: object) -> PageLayout:
    """Build a PageLayout from a layout name or inline layout spec."""

    if spec is None:
        return default_page_layout("standard", theme)
    if isinstance(spec, str):
        return default_page_layout(spec, theme)

    layout_type = str(spec.get("type", spec.get("name", "layout.grid")))
    name = layout_type.removeprefix("layout.")
    base = default_page_layout(name if name in {"cover", "section", "blank", "closing", "qa"} else "standard", theme)
    grid = GridSpec(
        columns=int(spec.get("columns", base.grid.columns)),
        rows=int(spec.get("rows", base.grid.rows)),
        gap=float(spec.get("gap", base.grid.gap)),
    )
    return PageLayout(
        name=name,
        title_box=base.title_box,
        subtitle_box=base.subtitle_box,
        content_box=base.content_box,
        footer_box=base.footer_box,
        page_number_box=base.page_number_box,
        grid=grid,
        zones=base.zones,
    )


def resolve_block_box(layout: PageLayout, block_layout: Mapping[str, Any] | None) -> Box:
    """Resolve a block layout spec to a concrete Box."""

    content = layout.content_box or Box(0, 0, 0, 0)
    spec: Mapping[str, Any] = block_layout or {}
    mode = str(spec.get("mode", "grid" if "col" in spec or "row" in spec else "absolute"))

    if mode == "absolute":
        return Box(
            float(spec.get("x", content.x)),
            float(spec.get("y", content.y)),
            float(spec.get("w", content.w)),
            float(spec.get("h", content.h)),
        )

    if mode == "zone":
        zone = str(spec.get("zone", "content"))
        return layout.zones.get(zone, content)

    grid = layout.grid
    col = max(1, int(spec.get("col", 1)))
    span = max(1, int(spec.get("span", grid.columns)))
    row = max(1, int(spec.get("row", 1)))
    row_span = max(1, int(spec.get("row_span", 1)))

    col_w = (content.w - grid.gap * (grid.columns - 1)) / max(1, grid.columns)
    row_h = (content.h - grid.gap * (grid.rows - 1)) / max(1, grid.rows)
    x = content.x + (col - 1) * (col_w + grid.gap)
    y = content.y + (row - 1) * (row_h + grid.gap)
    w = col_w * span + grid.gap * (span - 1)
    h = row_h * row_span + grid.gap * (row_span - 1)
    return Box(x, y, w, h)
