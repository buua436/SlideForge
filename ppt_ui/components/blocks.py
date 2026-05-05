from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches

from ppt_ui.core.component import RenderContext
from ppt_ui.core.layout import Box


def _items(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _style(ctx: RenderContext, key: str, default: str) -> str:
    value = ctx.style.get(key)
    return str(value) if value not in (None, "") else default


def _style_num(ctx: RenderContext, key: str, default: float) -> float:
    value = ctx.style.get(key)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _color(ctx: RenderContext, value: object, default: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        raw = default
    colors = ctx.theme.colors
    resolved = getattr(colors, raw, raw)
    if re.match(r"^[0-9A-Fa-f]{6}$", str(resolved)):
        return f"#{resolved}"
    return str(resolved)


def _palette(ctx: RenderContext, fallback: list[str] | None = None) -> list[str]:
    palette = [str(color).strip().lstrip("#") for color in getattr(ctx.theme, "chart_palette", []) if str(color).strip()]
    return palette or fallback or [ctx.theme.colors.primary, ctx.theme.colors.accent, ctx.theme.colors.success, ctx.theme.colors.warning]


def _numbers(value: object) -> list[float]:
    if not isinstance(value, list):
        return []
    result: list[float] = []
    for item in value:
        try:
            result.append(float(item))
        except (TypeError, ValueError):
            result.append(0.0)
    return result


@dataclass
class TextComponent:
    text: str = ""
    bullets: list[str] = field(default_factory=list)
    size: int | None = None
    color: str | None = None
    bold: bool = False
    align: str = "left"
    valign: str = "top"

    def render(self, ctx: RenderContext, box: Box) -> None:
        if ctx.style.get("fill") or ctx.style.get("border"):
            ctx.renderer.add_card(
                ctx.slide,
                box,
                fill=_style(ctx, "fill", ctx.theme.colors.surface_white),
                line=_style(ctx, "border", ctx.theme.colors.border_light),
                shadow=bool(ctx.style.get("shadow", False)),
            )
            box = box.inset(0.18, 0.12)
        size = int(ctx.style.get("size", self.size or ctx.theme.fonts.body_size))
        color = _style(ctx, "color", self.color or ctx.theme.colors.text_secondary)
        bold = bool(ctx.style.get("bold", self.bold))
        align = str(ctx.style.get("align", self.align))
        valign = str(ctx.style.get("valign", self.valign))
        if self.bullets:
            ctx.renderer.bullet_list(ctx.slide, box, self.bullets, size=size, text_color=color, bullet_color=_style(ctx, "accent", ctx.theme.colors.primary))
            return
        ctx.renderer.text(
            ctx.slide,
            box,
            self.text,
            size=size,
            color=color,
            bold=bold,
            align=align,
            valign=valign,
        )

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "TextComponent":
        return cls(
            text=str(props.get("text", "")),
            bullets=[str(item) for item in props.get("bullets", [])],
            size=int(props["size"]) if props.get("size") is not None else None,
            color=str(props["color"]) if props.get("color") is not None else None,
            bold=bool(props.get("bold", False)),
            align=str(props.get("align", "left")),
            valign=str(props.get("valign", "top")),
        )


@dataclass
class MetricCardsComponent:
    cards: list[dict[str, Any]] = field(default_factory=list)

    def render(self, ctx: RenderContext, box: Box) -> None:
        count = max(1, len(self.cards))
        columns = min(count, 4)
        if box.w < 4.8 and columns > 2:
            columns = 2
        rows_count = max(1, (count + columns - 1) // columns)
        rows = box.split_rows(rows_count, ctx.theme.spacing.gutter)
        cells = [cell for row in rows for cell in row.split_cols(columns, ctx.theme.spacing.gutter)]
        for cell, card in zip(cells, self.cards):
            ctx.renderer.add_metric_card(
                ctx.slide,
                cell,
                label=str(card.get("label", "")),
                value=str(card.get("value", "")),
                delta=str(card.get("delta", "")),
                note=str(card.get("compare", card.get("note", ""))),
                icon=str(card.get("icon", ""))[:3].upper(),
                fill=_style(ctx, "fill", ctx.theme.component_style("metric_card").fill),
                border=_style(ctx, "border", ctx.theme.component_style("metric_card").border),
                accent=_style(ctx, "accent", ctx.theme.component_style("metric_card").accent),
            )

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "MetricCardsComponent":
        return cls(cards=_items(props.get("cards", [])))


@dataclass
class LineChartComponent:
    categories: list[str] = field(default_factory=list)
    series: list[dict[str, Any]] = field(default_factory=list)

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        r.add_card(ctx.slide, box, fill=_style(ctx, "fill", ctx.theme.colors.surface_white), line=_style(ctx, "border", ctx.theme.colors.border_light))
        chart = box.inset(0.34, 0.34, 0.28, 0.38)
        legend_h = 0.24 if self.series else 0.0
        plot = Box(chart.x + 0.45, chart.y + 0.25 + legend_h, chart.w - 0.65, chart.h - 0.78 - legend_h)
        values = [float(value) for item in self.series for value in item.get("values", [])]
        max_value = max(values) if values else 1
        min_value = min(0, min(values) if values else 0)
        span = max(max_value - min_value, 1)
        caption_size = ctx.theme.fonts.caption_size
        line_width = _style_num(ctx, "line_width", 1.3)

        for idx in range(5):
            y = plot.y + idx * plot.h / 4
            r.line(ctx.slide, plot.x, y, plot.x + plot.w, y, ctx.theme.colors.border_light, width=0.6)
            label = int(max_value - idx * span / 4)
            r.text(ctx.slide, Box(chart.x, y - 0.06, 0.34, 0.12), str(label), size=caption_size, color=ctx.theme.colors.text_tertiary, align="right")

        colors = _palette(ctx)
        category_count = max(1, len(self.categories) - 1)
        for series_idx, item in enumerate(self.series):
            color = str(item.get("color", "")) or colors[series_idx % len(colors)]
            points: list[tuple[float, float]] = []
            for idx, raw_value in enumerate(item.get("values", [])):
                value = float(raw_value)
                x = plot.x + idx * plot.w / category_count
                y = plot.y + plot.h - ((value - min_value) / span) * plot.h
                points.append((x, y))
                r.circle(ctx.slide, Box(x - 0.035, y - 0.035, 0.07, 0.07), color, line="FFFFFF")
            for start, end in zip(points, points[1:]):
                r.line(ctx.slide, start[0], start[1], end[0], end[1], color, width=line_width)

        for idx, label in enumerate(self.categories):
            x = plot.x + idx * plot.w / category_count
            r.text(ctx.slide, Box(x - 0.22, plot.y + plot.h + 0.12, 0.44, 0.12), label, size=caption_size, color=ctx.theme.colors.text_secondary, align="center")

        legend_width = min(chart.w - 0.72, max(1.20, len(self.series[:4]) * 1.32))
        legend_x = chart.x + chart.w - legend_width
        cursor_x = legend_x
        for idx, item in enumerate(self.series[:4]):
            color = str(item.get("color", "")) or colors[idx % len(colors)]
            name = str(item.get("name", ""))
            item_width = min(1.55, max(1.05, 0.36 + len(name) * 0.055))
            r.rect(ctx.slide, Box(cursor_x, chart.y + 0.07, 0.13, 0.04), color, rounded=True)
            r.text(ctx.slide, Box(cursor_x + 0.18, chart.y + 0.005, item_width - 0.18, 0.16), name, size=caption_size, color=ctx.theme.colors.text_secondary)
            cursor_x += item_width + 0.14

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "LineChartComponent":
        return cls(
            categories=[str(item) for item in props.get("categories", [])],
            series=_items(props.get("series", [])),
        )


@dataclass
class ComparisonTableComponent:
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    conclusion: str = ""

    def render(self, ctx: RenderContext, box: Box) -> None:
        table_box = box
        if self.conclusion:
            table_box = Box(box.x, box.y, box.w, max(0.2, box.h - 0.58))
        ctx.renderer.add_table(ctx.slide, table_box, self.headers, self.rows)
        if self.conclusion:
            conclusion_box = Box(box.x + 0.22, box.y + box.h - 0.42, box.w - 0.44, 0.32)
            ctx.renderer.rect(ctx.slide, conclusion_box, ctx.theme.colors.primary_soft, line=ctx.theme.colors.border_light, rounded=True)
            ctx.renderer.text(ctx.slide, conclusion_box.inset(0.10, 0.05), self.conclusion, size=ctx.theme.fonts.caption_size, color=ctx.theme.colors.primary_dark, bold=True, align="center", valign="middle")

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "ComparisonTableComponent":
        rows: list[list[str]] = []
        for row in props.get("rows", []):
            if isinstance(row, Sequence) and not isinstance(row, str):
                rows.append([str(value) for value in row])
        return cls(
            headers=[str(item) for item in props.get("headers", [])],
            rows=rows,
            conclusion=str(props.get("conclusion", "")),
        )


@dataclass
class TimelineComponent:
    items: list[dict[str, Any]] = field(default_factory=list)

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        r.add_card(ctx.slide, box, fill=_style(ctx, "fill", ctx.theme.colors.surface_white), line=_style(ctx, "border", ctx.theme.colors.border_light))
        inner = box.inset(0.30, 0.35, 0.30, 0.30)
        line_y = inner.y + 0.18
        r.line(ctx.slide, inner.x + 0.25, line_y, inner.x + inner.w - 0.25, line_y, color=ctx.theme.colors.border, width=1.0)
        slots = inner.split_cols(max(1, len(self.items)), 0.14)
        for slot, item in zip(slots, self.items):
            r.add_status_timeline_node(
                ctx.slide,
                slot,
                label=str(item.get("label", "")),
                date=str(item.get("date", "")),
                description=str(item.get("description", "")),
                status=str(item.get("status", "normal")),
            )

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "TimelineComponent":
        return cls(items=_items(props.get("items", [])))


@dataclass
class BarChartComponent:
    categories: list[str] = field(default_factory=list)
    series: list[dict[str, Any]] = field(default_factory=list)

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        r.add_card(ctx.slide, box, fill=_style(ctx, "fill", ctx.theme.colors.surface_white), line=_style(ctx, "border", ctx.theme.colors.border_light))
        chart = box.inset(0.34, 0.34, 0.28, 0.34)
        plot = Box(chart.x + 0.45, chart.y + 0.38, chart.w - 0.62, chart.h - 0.86)
        colors = _palette(ctx)
        values = [value for item in self.series for value in _numbers(item.get("values", []))]
        max_value = max(values) if values else 1.0
        caption_size = ctx.theme.fonts.caption_size

        for idx in range(4):
            y = plot.y + idx * plot.h / 3
            r.line(ctx.slide, plot.x, y, plot.x + plot.w, y, ctx.theme.colors.border_light, width=0.5)
        groups = max(1, len(self.categories))
        group_w = plot.w / groups
        series_count = max(1, len(self.series))
        bar_w = min(0.20, group_w / (series_count + 1.2))
        for series_idx, item in enumerate(self.series):
            color = str(item.get("color", "")) or colors[series_idx % len(colors)]
            for idx, value in enumerate(_numbers(item.get("values", []))[:groups]):
                h = (value / max_value) * plot.h if max_value else 0
                x = plot.x + idx * group_w + (group_w - bar_w * series_count) / 2 + series_idx * bar_w
                y = plot.y + plot.h - h
                r.rect(ctx.slide, Box(x, y, bar_w * 0.82, h), color, rounded=True)
        for idx, label in enumerate(self.categories):
            x = plot.x + idx * group_w + group_w / 2
            r.text(ctx.slide, Box(x - 0.28, plot.y + plot.h + 0.12, 0.56, 0.12), label, size=caption_size, color=ctx.theme.colors.text_secondary, align="center")
        cursor_x = chart.x + chart.w - min(2.8, len(self.series) * 1.20)
        for idx, item in enumerate(self.series[:3]):
            color = str(item.get("color", "")) or colors[idx % len(colors)]
            r.rect(ctx.slide, Box(cursor_x, chart.y + 0.06, 0.13, 0.04), color, rounded=True)
            r.text(ctx.slide, Box(cursor_x + 0.18, chart.y, 0.92, 0.16), str(item.get("name", "")), size=caption_size, color=ctx.theme.colors.text_secondary)
            cursor_x += 1.10

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "BarChartComponent":
        return cls(categories=[str(item) for item in props.get("categories", [])], series=_items(props.get("series", [])))


@dataclass
class PieChartComponent:
    labels: list[str] = field(default_factory=list)
    values: list[float] = field(default_factory=list)
    donut: bool = False

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        r.add_card(ctx.slide, box, fill=_style(ctx, "fill", ctx.theme.colors.surface_white), line=_style(ctx, "border", ctx.theme.colors.border_light))
        inner = box.inset(0.22, 0.22, 0.22, 0.22)
        data = CategoryChartData()
        labels = self.labels or [f"Item {idx + 1}" for idx in range(len(self.values))]
        values = self.values or [1.0]
        data.categories = labels[: len(values)]
        data.add_series("Share", values)
        chart_type = XL_CHART_TYPE.DOUGHNUT if self.donut else XL_CHART_TYPE.PIE
        legend_w = min(1.05, inner.w * 0.38) if inner.w >= 2.1 else 0.0
        chart_box = Box(inner.x, inner.y + 0.05, inner.w - legend_w - 0.08, inner.h - 0.10)
        chart_shape = ctx.slide.shapes.add_chart(chart_type, Inches(chart_box.x), Inches(chart_box.y), Inches(chart_box.w), Inches(chart_box.h), data)
        chart = chart_shape.chart
        chart.has_legend = False
        chart.has_title = False
        colors = _palette(ctx)
        try:
            for idx, point in enumerate(chart.series[0].points):
                point.format.fill.solid()
                point.format.fill.fore_color.rgb = r.rgb(colors[idx % len(colors)])
        except (AttributeError, IndexError):
            pass
        if legend_w:
            total = sum(values) or 1.0
            rows = Box(inner.x + inner.w - legend_w, inner.y + 0.35, legend_w, inner.h - 0.70).split_rows(max(1, len(labels)), 0.04)
            for idx, (row, label) in enumerate(zip(rows, labels)):
                color = colors[idx % len(colors)]
                r.rect(ctx.slide, Box(row.x, row.y + 0.04, 0.10, 0.08), color, rounded=True)
                pct = values[idx] / total * 100 if idx < len(values) else 0
                r.text(ctx.slide, Box(row.x + 0.16, row.y, row.w - 0.16, 0.12), str(label), size=ctx.theme.fonts.caption_size, color=ctx.theme.colors.text_primary, bold=True)
                r.text(ctx.slide, Box(row.x + 0.16, row.y + 0.13, row.w - 0.16, 0.10), f"{pct:.0f}%", size=max(6, ctx.theme.fonts.caption_size - 1), color=ctx.theme.colors.text_tertiary)

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "PieChartComponent":
        values = _numbers(props.get("values", props.get("data", [])))
        labels = [str(item) for item in props.get("labels", props.get("categories", []))]
        return cls(labels=labels, values=values, donut=bool(props.get("donut", False)))


@dataclass
class ProgressBarsComponent:
    items: list[dict[str, Any]] = field(default_factory=list)

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        r.add_card(ctx.slide, box, fill=_style(ctx, "fill", ctx.theme.colors.surface_white), line=_style(ctx, "border", ctx.theme.colors.border_light))
        rows = box.inset(0.30, 0.28).split_rows(max(1, len(self.items)), 0.08)
        for row, item in zip(rows, self.items):
            label = str(item.get("label", ""))
            value = max(0.0, min(100.0, float(item.get("value", 0))))
            color = str(item.get("color", "")) or ctx.theme.colors.primary
            r.text(ctx.slide, Box(row.x, row.y + 0.02, 1.35, 0.18), label, size=ctx.theme.fonts.caption_size, color=ctx.theme.colors.text_primary, bold=True)
            track = Box(row.x + 1.50, row.y + 0.08, row.w - 2.10, 0.08)
            r.rect(ctx.slide, track, ctx.theme.colors.gray_100, rounded=True)
            r.rect(ctx.slide, Box(track.x, track.y, track.w * value / 100, track.h), color, rounded=True)
            r.text(ctx.slide, Box(row.x + row.w - 0.48, row.y + 0.02, 0.48, 0.16), f"{value:.0f}%", size=8, color=ctx.theme.colors.text_secondary, align="right")

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "ProgressBarsComponent":
        return cls(items=_items(props.get("items", [])))


@dataclass
class ProcessFlowComponent:
    steps: list[dict[str, Any]] = field(default_factory=list)

    def render(self, ctx: RenderContext, box: Box) -> None:
        steps = self.steps[:6]
        if not steps:
            return
        r = ctx.renderer
        r.add_card(ctx.slide, box, fill=_style(ctx, "fill", ctx.theme.colors.surface_white), line=_style(ctx, "border", ctx.theme.colors.border_light))
        inner = box.inset(0.22, 0.34, 0.22, 0.28)
        cells = inner.split_cols(len(steps), 0.16)
        for idx, (cell, step) in enumerate(zip(cells, steps), start=1):
            card_h = min(cell.h, 1.55)
            card_y = cell.y + max(0, (cell.h - card_h) / 2)
            step_box = Box(cell.x, card_y, cell.w, card_h)
            r.add_process_step_card(
                ctx.slide,
                step_box,
                index=idx,
                title=str(step.get("title", step.get("label", ""))),
                description=str(step.get("description", "")),
                output=str(step.get("output", "")),
            )
            if idx < len(cells):
                x = cell.x + cell.w + 0.03
                y = card_y + card_h / 2
                r.line(ctx.slide, x, y, x + 0.10, y, ctx.theme.colors.primary, width=0.8)

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "ProcessFlowComponent":
        return cls(steps=_items(props.get("steps", props.get("items", []))))


@dataclass
class RoadmapComponent:
    items: list[dict[str, Any]] = field(default_factory=list)

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        r.add_card(ctx.slide, box, fill=_style(ctx, "fill", ctx.theme.colors.surface_white), line=_style(ctx, "border", ctx.theme.colors.border_light))
        inner = box.inset(0.34, 0.30)
        rows = inner.split_rows(max(1, len(self.items)), 0.10)
        colors = _palette(ctx)
        for idx, (row, item) in enumerate(zip(rows, self.items)):
            color = str(item.get("color", "")) or colors[idx % len(colors)]
            r.text(ctx.slide, Box(row.x, row.y + 0.02, 1.0, 0.18), str(item.get("label", "")), size=8, color=ctx.theme.colors.text_primary, bold=True)
            track = Box(row.x + 1.10, row.y + 0.08, row.w - 1.55, 0.07)
            r.rect(ctx.slide, track, ctx.theme.colors.gray_100, rounded=True)
            start = max(0.0, min(1.0, float(item.get("start", 0))))
            end = max(start + 0.05, min(1.0, float(item.get("end", 1))))
            r.rect(ctx.slide, Box(track.x + track.w * start, track.y, track.w * (end - start), track.h), color, rounded=True)
            r.text(ctx.slide, Box(row.x + row.w - 0.40, row.y + 0.01, 0.40, 0.16), str(item.get("period", "")), size=7, color=ctx.theme.colors.text_tertiary, align="right")

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "RoadmapComponent":
        return cls(items=_items(props.get("items", [])))


@dataclass
class IconComponent:
    name: str = ""
    label: str = ""
    source: str = ""
    description: str = ""
    src: str = ""
    color: str = ""
    size: int | None = None
    width: int | None = None
    height: int | None = None
    rotate: str | int | None = None
    flip: str = ""
    stroke_width: float | None = None
    opacity: float = 1.0

    def _render_mark(self, ctx: RenderContext, icon_box: Box, accent: str, fallback: str, *, size: int = 9) -> None:
        if self.src and ctx.renderer.picture(ctx.slide, self.src, icon_box.inset(0.08, 0.08), fit="contain") is not None:
            return
        request = ctx.renderer.icon_registry.create_request(
            self.name,
            color=accent,
            size=self.size or self.width or self.height or 128,
            width=self.width,
            height=self.height,
            rotate=self.rotate,
            flip=self.flip,
            stroke_width=self.stroke_width,
        )
        if request is not None and ctx.renderer.icon_picture(ctx.slide, request, icon_box.inset(0.08, 0.08), opacity=self.opacity) is not None:
            return
        ctx.renderer.text(ctx.slide, icon_box.inset(0.03, 0.02), fallback, size=size, color=accent, bold=True, align="center", valign="middle")

    def render(self, ctx: RenderContext, box: Box) -> None:
        r = ctx.renderer
        fill = _style(ctx, "fill", ctx.theme.colors.primary_soft)
        accent = _color(ctx, self.color or ctx.style.get("accent"), ctx.theme.colors.primary)
        r.add_card(ctx.slide, box, fill=fill, line=_style(ctx, "border", ctx.theme.colors.border_light), shadow=bool(ctx.style.get("shadow", False)))
        icon_text = self.label or self.name.split(":")[-1][:2].upper()
        if box.h < 1.15:
            center_y = box.y + box.h / 2 - (0.10 if self.name else 0)
            icon_box = Box(box.x + box.w / 2 - 0.20, center_y - 0.20, 0.40, 0.40)
            r.circle(ctx.slide, icon_box, "FFFFFF", line=ctx.theme.colors.border_light)
            self._render_mark(ctx, icon_box, accent, icon_text, size=8)
            if self.name:
                r.text(ctx.slide, Box(box.x + 0.10, center_y + 0.30, box.w - 0.20, 0.14), self.name, size=7, color=ctx.theme.colors.text_secondary, align="center")
            return

        inner = box.inset(0.22, 0.18)
        icon_box = Box(inner.x, inner.y + 0.02, 0.48, 0.48)
        r.circle(ctx.slide, icon_box, "FFFFFF", line=ctx.theme.colors.border_light)
        self._render_mark(ctx, icon_box, accent, icon_text, size=9)
        title = self.source or self.name.split(":")[0].title() or "Icon"
        r.text(ctx.slide, Box(inner.x + 0.62, inner.y + 0.04, inner.w - 0.62, 0.20), title, size=ctx.theme.fonts.caption_size, color=ctx.theme.colors.text_primary, bold=True)
        r.text(ctx.slide, Box(inner.x + 0.62, inner.y + 0.28, inner.w - 0.62, 0.14), self.name, size=7, color=ctx.theme.colors.text_tertiary)
        if self.description:
            r.text(ctx.slide, Box(inner.x, inner.y + 0.72, inner.w, inner.h - 0.72), self.description, size=8, color=ctx.theme.colors.text_secondary)

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "IconComponent":
        return cls(
            name=str(props.get("name", "")),
            label=str(props.get("label", "")),
            source=str(props.get("source", "")),
            description=str(props.get("description", "")),
            src=str(props.get("src", "")),
            color=str(props.get("color", "")),
            size=int(props["size"]) if props.get("size") is not None else None,
            width=int(props["width"]) if props.get("width") is not None else None,
            height=int(props["height"]) if props.get("height") is not None else None,
            rotate=props.get("rotate"),
            flip=str(props.get("flip", "")),
            stroke_width=float(props["stroke_width"]) if props.get("stroke_width") is not None else (float(props["strokeWidth"]) if props.get("strokeWidth") is not None else None),
            opacity=float(props.get("opacity", 1.0)),
        )


@dataclass
class ImageComponent:
    src: str = ""
    fit: str = "contain"

    def render(self, ctx: RenderContext, box: Box) -> None:
        path = Path(self.src)
        if not path.exists():
            ctx.renderer.add_card(ctx.slide, box, fill=ctx.theme.colors.gray_50, line=ctx.theme.colors.border_light)
            ctx.renderer.text(ctx.slide, box.inset(0.18, 0.16), f"Missing image: {self.src}", size=8, color=ctx.theme.colors.text_tertiary, align="center", valign="middle")
            return
        ctx.renderer.picture(ctx.slide, path, box, fit=self.fit)

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "ImageComponent":
        return cls(src=str(props.get("src", "")), fit=str(props.get("fit", "contain")))
