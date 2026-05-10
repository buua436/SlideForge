from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ppt_ui.core.component import Component, RenderContext
from ppt_ui.core.layout import Box
from ppt_ui.primitives import ChartPrimitive, ChartSeries, Group, Primitive, Rect, Text, normalize_class_names
from ppt_ui.styles import Style


def _items(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _numbers(value: object) -> tuple[float, ...]:
    if not isinstance(value, list | tuple):
        return ()
    result = []
    for item in value:
        try:
            result.append(float(item))
        except (TypeError, ValueError):
            result.append(0.0)
    return tuple(result)


def _class_names(ctx: RenderContext, props: Mapping[str, Any], *defaults: str) -> tuple[str, ...]:
    value = props.get("class_names", props.get("classes", props.get("class")))
    return (*defaults, *(normalize_class_names(value) or ctx.class_names))


def _primitive_id(ctx: RenderContext, props: Mapping[str, Any]) -> str | None:
    value = props.get("id", ctx.block_id)
    return str(value) if value is not None else None


@dataclass
class ChartComponent(Component):
    chart_type: str = "line"
    props: dict[str, Any] = field(default_factory=dict)

    def render_to_primitives(self, ctx: RenderContext, box: Box) -> Group:
        title = str(self.props.get("title", ""))
        subtitle = str(self.props.get("subtitle", ""))
        pad = float(ctx.style.get("padding", 0.24) or 0.24)
        title_h = 0.34 if title else 0.0
        subtitle_h = 0.22 if subtitle else 0.0
        chart_box = box.inset(pad, pad + title_h + subtitle_h, pad, pad)
        children: list[Primitive] = [
            Rect(
                class_names=("chart-surface",),
                box=box,
                style=Style(fill="{colors.surface_white}", stroke="{colors.border}", radius="{radius.md}", shadow=True),
            )
        ]
        if title:
            children.append(
                Text(
                    class_names=("chart-title",),
                    box=Box(box.x + pad, box.y + pad - 0.02, box.w - pad * 2, 0.24),
                    text=title,
                    style=Style(color="{colors.text_primary}", font_size=ctx.theme.fonts.body_size, font_weight="bold"),
                )
            )
        if subtitle:
            children.append(
                Text(
                    class_names=("chart-subtitle",),
                    box=Box(box.x + pad, box.y + pad + 0.25, box.w - pad * 2, 0.18),
                    text=subtitle,
                    style=Style(color="{colors.text_secondary}", font_size=ctx.theme.fonts.caption_size),
                )
            )
        children.append(self._chart_primitive(ctx, chart_box))
        return Group(id=_primitive_id(ctx, self.props), class_names=_class_names(ctx, self.props, "chart", f"chart-{self.chart_type}"), children=tuple(children))

    def _chart_primitive(self, ctx: RenderContext, box: Box) -> ChartPrimitive:
        if self.chart_type in {"pie", "donut"}:
            return ChartPrimitive(
                class_names=("chart-plot",),
                box=box,
                chart_type=self.chart_type,
                labels=tuple(str(item) for item in self.props.get("labels", self.props.get("categories", ()))),
                values=_numbers(self.props.get("values", self.props.get("data", ()))),
                style=Style(stroke_width=float(ctx.style.get("line_width", 1.5) or 1.5)),
            )

        series = []
        for item in _items(self.props.get("series", [])):
            series.append(ChartSeries(str(item.get("name", "")), _numbers(item.get("values", ()))))
        return ChartPrimitive(
            class_names=("chart-plot",),
            box=box,
            chart_type=self.chart_type,
            categories=tuple(str(item) for item in self.props.get("categories", ())),
            series=tuple(series),
            style=Style(stroke_width=float(ctx.style.get("line_width", 1.5) or 1.5)),
        )

    @classmethod
    def from_props(cls, props: Mapping[str, Any], *, chart_type: str = "line") -> "ChartComponent":
        return cls(chart_type=chart_type, props=dict(props))
