from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from ppt_ui.core.component import Component, RenderContext
from ppt_ui.core.layout import Box
from ppt_ui.primitives import Group, Primitive, Rect, TablePrimitive, Text, normalize_class_names
from ppt_ui.styles import Style


def _class_names(ctx: RenderContext, props: Mapping[str, Any], *defaults: str) -> tuple[str, ...]:
    value = props.get("class_names", props.get("classes", props.get("class")))
    return (*defaults, *(normalize_class_names(value) or ctx.class_names))


def _primitive_id(ctx: RenderContext, props: Mapping[str, Any]) -> str | None:
    value = props.get("id", ctx.block_id)
    return str(value) if value is not None else None


@dataclass
class TableComponent(Component):
    props: dict[str, Any] = field(default_factory=dict)
    variant: str = "basic"

    def render_to_primitives(self, ctx: RenderContext, box: Box) -> Primitive:
        headers = tuple(str(item) for item in self.props.get("headers", ()))
        rows = []
        for row in self.props.get("rows", []):
            if isinstance(row, Sequence) and not isinstance(row, str):
                rows.append(tuple(str(cell) for cell in row))
        conclusion = str(self.props.get("conclusion", ""))

        if not conclusion:
            return TablePrimitive(
                id=_primitive_id(ctx, self.props),
                class_names=_class_names(ctx, self.props, "table", f"table-{self.variant}"),
                box=box,
                headers=headers,
                rows=tuple(rows),
                style=Style.from_dict(ctx.style),
            )

        table_box = Box(box.x, box.y, box.w, max(0.2, box.h - 0.58))
        conclusion_box = Box(box.x + 0.22, box.y + box.h - 0.42, box.w - 0.44, 0.32)
        return Group(
            id=_primitive_id(ctx, self.props),
            class_names=_class_names(ctx, self.props, "table", f"table-{self.variant}"),
            children=(
                TablePrimitive(box=table_box, headers=headers, rows=tuple(rows), style=Style.from_dict(ctx.style)),
                Rect(class_names=("table-conclusion-bg",), box=conclusion_box, style=Style(fill="{colors.primary_soft}", stroke="{colors.border_light}", radius=0.05)),
                Text(class_names=("table-conclusion",), box=conclusion_box.inset(0.10, 0.05), text=conclusion, style=Style(color="{colors.primary_dark}", font_size=ctx.theme.fonts.caption_size, font_weight="bold", align="center", valign="middle")),
            ),
        )

    @classmethod
    def from_props(cls, props: Mapping[str, Any], *, variant: str = "basic") -> "TableComponent":
        return cls(props=dict(props), variant=variant)
