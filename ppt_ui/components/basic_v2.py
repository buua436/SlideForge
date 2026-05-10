from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ppt_ui.core.component import Component, RenderContext
from ppt_ui.core.layout import Box
from ppt_ui.primitives import Ellipse, Group, Line, Primitive, Rect, Text, normalize_class_names
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


def _class_names(ctx: RenderContext, props: Mapping[str, Any], *defaults: str) -> tuple[str, ...]:
    value = props.get("class_names", props.get("classes", props.get("class")))
    return (*defaults, *(normalize_class_names(value) or ctx.class_names))


def _primitive_id(ctx: RenderContext, props: Mapping[str, Any]) -> str | None:
    value = props.get("id", ctx.block_id)
    return str(value) if value is not None else None


@dataclass
class BasicTextComponent(Component):
    text: str = ""
    bullets: list[str] = field(default_factory=list)
    props: dict[str, Any] = field(default_factory=dict)

    def render_to_primitives(self, ctx: RenderContext, box: Box) -> Primitive:
        style = Style.from_dict(_style_data(ctx, self.props))
        if not self.bullets:
            return Text(
                id=_primitive_id(ctx, self.props),
                class_names=_class_names(ctx, self.props, "text"),
                box=box,
                text=self.text,
                style=style,
            )

        rows = box.split_rows(max(1, len(self.bullets)), gutter=0.04)
        children: list[Primitive] = []
        for index, (row, item) in enumerate(zip(rows, self.bullets)):
            children.append(
                Ellipse(
                    class_names=("bullet-dot",),
                    box=Box(row.x, row.y + 0.08, 0.07, 0.07),
                    style=Style(fill=style.extras.get("accent", "{colors.primary}") if style.extras else "{colors.primary}"),
                )
            )
            children.append(
                Text(
                    id=_primitive_id(ctx, self.props) if index == 0 else None,
                    class_names=_class_names(ctx, self.props, "text", "bullet-text"),
                    box=Box(row.x + 0.16, row.y, row.w - 0.16, row.h),
                    text=item,
                    style=style,
                )
            )
        return Group(id=_primitive_id(ctx, self.props), class_names=_class_names(ctx, self.props, "text-list"), children=tuple(children))

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "BasicTextComponent":
        return cls(
            text=str(props.get("text", "")),
            bullets=[str(item) for item in props.get("bullets", [])],
            props=dict(props),
        )


@dataclass
class BasicCardComponent(Component):
    props: dict[str, Any] = field(default_factory=dict)

    def render_to_primitives(self, ctx: RenderContext, box: Box) -> Rect:
        return Rect(
            id=_primitive_id(ctx, self.props),
            class_names=_class_names(ctx, self.props, "card"),
            box=box,
            style=Style.from_dict(_style_data(ctx, self.props)),
        )

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "BasicCardComponent":
        return cls(props=dict(props))


@dataclass
class BasicDividerComponent(Component):
    props: dict[str, Any] = field(default_factory=dict)

    def render_to_primitives(self, ctx: RenderContext, box: Box) -> Line:
        return Line(
            id=_primitive_id(ctx, self.props),
            class_names=_class_names(ctx, self.props, "divider"),
            box=box,
            x1=float(self.props.get("x1", 0.0)),
            y1=float(self.props.get("y1", 0.0)),
            x2=float(self.props.get("x2", 0.0)),
            y2=float(self.props.get("y2", 0.0)),
            style=Style.from_dict(_style_data(ctx, self.props)),
        )

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "BasicDividerComponent":
        return cls(props=dict(props))
