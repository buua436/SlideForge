from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ppt_ui.core.component import Component, RenderContext
from ppt_ui.core.layout import Box
from ppt_ui.primitives import (
    ChartPrimitive,
    ChartSeries,
    IconPrimitive,
    ImagePrimitive,
    Line,
    Rect,
    TablePrimitive,
    Text,
    normalize_class_names,
)
from ppt_ui.styles import Style


def _style_data(ctx: RenderContext, props: Mapping[str, Any]) -> dict[str, Any]:
    data = dict(ctx.style)
    for key in (
        "fill",
        "stroke",
        "border",
        "color",
        "font_size",
        "size",
        "font_family",
        "font_weight",
        "bold",
        "radius",
        "opacity",
        "shadow",
        "padding",
        "align",
        "valign",
        "stroke_width",
        "line_width",
        "line_spacing",
        "overflow",
        "max_chars",
    ):
        if key in props:
            data[key] = props[key]
    if isinstance(props.get("style"), Mapping):
        data.update(dict(props["style"]))
    return data


def _class_names(ctx: RenderContext, props: Mapping[str, Any]) -> tuple[str, ...]:
    value = props.get("class_names", props.get("classes", props.get("class")))
    return normalize_class_names(value) or ctx.class_names


def _primitive_id(ctx: RenderContext, props: Mapping[str, Any]) -> str | None:
    value = props.get("id", ctx.block_id)
    return str(value) if value is not None else None


@dataclass
class PrimitiveTextComponent(Component):
    props: dict[str, Any] = field(default_factory=dict)

    def render_to_primitives(self, ctx: RenderContext, box: Box) -> Text:
        return Text(
            id=_primitive_id(ctx, self.props),
            class_names=_class_names(ctx, self.props),
            box=box,
            text=str(self.props.get("text", "")),
            style=Style.from_dict(_style_data(ctx, self.props)),
        )

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "PrimitiveTextComponent":
        return cls(props=dict(props))


@dataclass
class PrimitiveRectComponent(Component):
    props: dict[str, Any] = field(default_factory=dict)

    def render_to_primitives(self, ctx: RenderContext, box: Box) -> Rect:
        return Rect(
            id=_primitive_id(ctx, self.props),
            class_names=_class_names(ctx, self.props),
            box=box,
            style=Style.from_dict(_style_data(ctx, self.props)),
        )

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "PrimitiveRectComponent":
        return cls(props=dict(props))


@dataclass
class PrimitiveLineComponent(Component):
    props: dict[str, Any] = field(default_factory=dict)

    def render_to_primitives(self, ctx: RenderContext, box: Box) -> Line:
        return Line(
            id=_primitive_id(ctx, self.props),
            class_names=_class_names(ctx, self.props),
            box=box,
            x1=float(self.props.get("x1", 0.0)),
            y1=float(self.props.get("y1", 0.0)),
            x2=float(self.props.get("x2", 0.0)),
            y2=float(self.props.get("y2", 0.0)),
            style=Style.from_dict(_style_data(ctx, self.props)),
        )

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "PrimitiveLineComponent":
        return cls(props=dict(props))


@dataclass
class PrimitiveImageComponent(Component):
    props: dict[str, Any] = field(default_factory=dict)

    def render_to_primitives(self, ctx: RenderContext, box: Box) -> ImagePrimitive:
        return ImagePrimitive(
            id=_primitive_id(ctx, self.props),
            class_names=_class_names(ctx, self.props),
            box=box,
            src=str(self.props.get("src", "")),
            fit=str(self.props.get("fit", "contain")),
            alt=str(self.props.get("alt", "")),
            style=Style.from_dict(_style_data(ctx, self.props)),
        )

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "PrimitiveImageComponent":
        return cls(props=dict(props))


@dataclass
class PrimitiveIconComponent(Component):
    props: dict[str, Any] = field(default_factory=dict)

    def render_to_primitives(self, ctx: RenderContext, box: Box) -> IconPrimitive:
        icon_props = {key: value for key, value in self.props.items() if key in {"size", "width", "height", "rotate", "flip", "stroke_width"}}
        return IconPrimitive(
            id=_primitive_id(ctx, self.props),
            class_names=_class_names(ctx, self.props),
            box=box,
            name=str(self.props.get("name", "")),
            provider=str(self.props["provider"]) if self.props.get("provider") is not None else None,
            icon_props=icon_props,
            style=Style.from_dict(_style_data(ctx, self.props)),
        )

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "PrimitiveIconComponent":
        return cls(props=dict(props))


@dataclass
class PrimitiveTableComponent(Component):
    props: dict[str, Any] = field(default_factory=dict)

    def render_to_primitives(self, ctx: RenderContext, box: Box) -> TablePrimitive:
        rows: list[tuple[str, ...]] = []
        for row in self.props.get("rows", []):
            if isinstance(row, Sequence) and not isinstance(row, str):
                rows.append(tuple(str(cell) for cell in row))
        return TablePrimitive(
            id=_primitive_id(ctx, self.props),
            class_names=_class_names(ctx, self.props),
            box=box,
            headers=tuple(str(item) for item in self.props.get("headers", ())),
            rows=tuple(rows),
            style=Style.from_dict(_style_data(ctx, self.props)),
        )

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "PrimitiveTableComponent":
        return cls(props=dict(props))


@dataclass
class PrimitiveChartComponent(Component):
    props: dict[str, Any] = field(default_factory=dict)

    def render_to_primitives(self, ctx: RenderContext, box: Box) -> ChartPrimitive:
        series = []
        for item in self.props.get("series", []):
            if isinstance(item, Mapping):
                series.append(ChartSeries(str(item.get("name", "")), tuple(float(value) for value in item.get("values", ()))))
        return ChartPrimitive(
            id=_primitive_id(ctx, self.props),
            class_names=_class_names(ctx, self.props),
            box=box,
            chart_type=str(self.props.get("chart_type", self.props.get("kind", "line"))),
            categories=tuple(str(item) for item in self.props.get("categories", ())),
            series=tuple(series),
            labels=tuple(str(item) for item in self.props.get("labels", ())),
            values=tuple(float(item) for item in self.props.get("values", ())),
            options=dict(self.props.get("options", {})) if isinstance(self.props.get("options"), Mapping) else None,
            style=Style.from_dict(_style_data(ctx, self.props)),
        )

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "PrimitiveChartComponent":
        return cls(props=dict(props))
