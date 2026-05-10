from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ppt_ui.core.component import Component, ComponentSlot, RenderContext
from ppt_ui.core.layout import Box
from ppt_ui.primitives import Ellipse, Group, Primitive, Rect, Text, normalize_class_names
from ppt_ui.styles import Style


def _items(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _style_data(ctx: RenderContext, props: Mapping[str, Any]) -> dict[str, Any]:
    data = dict(ctx.style)
    if isinstance(props.get("style"), Mapping):
        data.update(dict(props["style"]))
    for key in ("fill", "stroke", "border", "color", "radius", "shadow", "opacity", "stroke_width"):
        if key in props:
            data[key] = props[key]
    return data


def _class_names(ctx: RenderContext, props: Mapping[str, Any], *defaults: str) -> tuple[str, ...]:
    value = props.get("class_names", props.get("classes", props.get("class")))
    return (*defaults, *(normalize_class_names(value) or ctx.class_names))


def _primitive_id(ctx: RenderContext, props: Mapping[str, Any]) -> str | None:
    value = props.get("id", ctx.block_id)
    return str(value) if value is not None else None


def _delta_color(delta: str) -> str:
    if delta.startswith("+"):
        return "{colors.success}"
    if delta.startswith("-"):
        return "{colors.warning}"
    return "{colors.text_tertiary}"


def _is_bare(ctx: RenderContext, props: Mapping[str, Any]) -> bool:
    variant = str(props.get("variant", ctx.style.get("variant", ""))).lower()
    return (
        variant in {"bare", "plain", "unstyled"}
        or bool(props.get("bare", False))
        or props.get("surface") is False
        or props.get("container") is False
        or ctx.style.get("surface") is False
        or ctx.style.get("container") is False
    )


def _slot_meta(slot: str) -> dict[str, str]:
    return {"component_type": "data.metric_card", "slot": slot}


@dataclass
class DataMetricCardComponent(Component):
    props: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def slot_contract(cls) -> tuple[ComponentSlot, ...]:
        return (
            ComponentSlot("root", role="container", required=True, description="Outer component area."),
            ComponentSlot("surface", role="surface", description="Optional card surface; omitted in bare mode."),
            ComponentSlot("label", role="text", required=True, description="Metric label."),
            ComponentSlot("value", role="text", required=True, description="Primary metric value."),
            ComponentSlot("delta", role="text", description="Change indicator."),
            ComponentSlot("compare", role="text", description="Comparison or note text."),
            ComponentSlot("icon", role="icon", description="Optional icon or short icon placeholder."),
        )

    def render_to_primitives(self, ctx: RenderContext, box: Box) -> Group:
        label = str(self.props.get("label", ""))
        value = str(self.props.get("value", ""))
        delta = str(self.props.get("delta", ""))
        compare = str(self.props.get("compare", self.props.get("note", "")))
        icon = str(self.props.get("icon", ""))[:2].upper()
        style = Style.from_dict(_style_data(ctx, self.props))
        pad = ctx.theme.spacing.card_padding
        bare = _is_bare(ctx, self.props)
        inner = box.inset(0.02, 0.02, 0.02, 0.02) if bare else box.inset(pad, 0.18, pad, 0.14)
        compact = box.h < 1.35

        children: list[Primitive] = []
        if not bare:
            children.append(
                Rect(
                    class_names=("metric-card-surface",),
                    box=box,
                    metadata=_slot_meta("surface"),
                    style=Style(
                        fill=style.fill or "{colors.surface_white}",
                        stroke=style.stroke or "{colors.border}",
                        radius=style.radius or "{radius.md}",
                        shadow=style.shadow if style.shadow is not None else True,
                    ),
                )
            )
        children.extend(
            [
                Text(
                    class_names=("metric-label",),
                    box=Box(inner.x, inner.y + 0.02, inner.w - 0.45, 0.22),
                    text=label,
                    metadata=_slot_meta("label"),
                    style=Style(color="{colors.text_secondary}", font_size=max(8, ctx.theme.fonts.caption_size - (1 if compact else 0)), font_weight="bold"),
                ),
                Text(
                    class_names=("metric-value",),
                    box=Box(inner.x, inner.y + (0.34 if compact else 0.42), inner.w, 0.38),
                    text=value,
                    metadata=_slot_meta("value"),
                    style=Style(color="{colors.text_primary}", font_size=19 if compact else 23, font_weight="bold"),
                ),
            ]
        )

        if icon:
            icon_box = Box(inner.x + inner.w - 0.34, inner.y, 0.28, 0.28)
            children.extend(
                [
                    Ellipse(class_names=("metric-icon-bg",), box=icon_box, metadata=_slot_meta("icon"), style=Style(fill="{colors.primary_soft}", stroke="{colors.border_light}")),
                    Text(class_names=("metric-icon",), box=icon_box.inset(0.03, 0.02), text=icon, metadata=_slot_meta("icon"), style=Style(color=style.extras.get("accent", "{colors.primary}"), font_size=8, font_weight="bold", align="center", valign="middle")),
                ]
            )

        if delta:
            children.append(
                Text(
                    class_names=("metric-delta",),
                    box=Box(inner.x, inner.y + (0.78 if compact else 0.88), inner.w, 0.20),
                    text=delta,
                    metadata=_slot_meta("delta"),
                    style=Style(color=_delta_color(delta), font_size=9 if compact else 10, font_weight="bold"),
                )
            )
        if compare and inner.h >= 1.08:
            children.append(
                Text(
                    class_names=("metric-compare",),
                    box=Box(inner.x, min(inner.y + (0.98 if compact else 1.12), inner.y + inner.h - 0.20), inner.w, 0.18),
                    text=compare,
                    metadata=_slot_meta("compare"),
                    style=Style(color="{colors.text_tertiary}", font_size=ctx.theme.fonts.tiny_size),
                )
            )

        default_classes = ("metric-card", "metric-card-bare") if bare else ("metric-card",)
        return Group(id=_primitive_id(ctx, self.props), class_names=_class_names(ctx, self.props, *default_classes), children=tuple(children))

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "DataMetricCardComponent":
        return cls(props=dict(props))


@dataclass
class DataMetricCardsComponent(Component):
    cards: list[dict[str, Any]] = field(default_factory=list)
    props: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def slot_contract(cls) -> tuple[ComponentSlot, ...]:
        return (
            ComponentSlot("root", role="container", required=True, description="Outer collection area."),
            ComponentSlot("items", role="collection", required=True, description="Metric card item slots."),
        )

    def render_to_primitives(self, ctx: RenderContext, box: Box) -> Group:
        count = max(1, len(self.cards))
        columns = int(ctx.style.get("columns", 0) or 0)
        if columns <= 0:
            columns = min(count, 4)
            cell_w = (box.w - ctx.theme.spacing.gutter * (columns - 1)) / max(1, columns)
            if cell_w < 1.55 and columns > 2:
                columns = 2
        columns = max(1, min(columns, count))
        rows_count = max(1, (count + columns - 1) // columns)
        rows = box.split_rows(rows_count, ctx.theme.spacing.gutter)
        cells = [cell for row in rows for cell in row.split_cols(columns, ctx.theme.spacing.gutter)]

        children: list[Primitive] = []
        for index, (cell, card) in enumerate(zip(cells, self.cards)):
            card_ctx = ctx.with_block(block_id=f"{ctx.block_id}-{index}" if ctx.block_id else None, class_names=(*ctx.class_names, "metric-card-item"))
            merged_card = dict(card)
            for key in ("bare", "surface", "container", "variant"):
                if key in self.props and key not in merged_card:
                    merged_card[key] = self.props[key]
            children.append(DataMetricCardComponent(merged_card).render_to_primitives(card_ctx, cell))
        return Group(id=ctx.block_id, class_names=ctx.class_names or ("metric-cards",), children=tuple(children))

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "DataMetricCardsComponent":
        return cls(cards=_items(props.get("cards", [])), props=dict(props))


@dataclass
class DataProgressComponent(Component):
    items: list[dict[str, Any]] = field(default_factory=list)

    def render_to_primitives(self, ctx: RenderContext, box: Box) -> Group:
        surface = Rect(
            class_names=("progress-surface",),
            box=box,
            style=Style(fill="{colors.surface_white}", stroke="{colors.border}", radius="{radius.md}", shadow=True),
        )
        rows = box.inset(0.30, 0.28).split_rows(max(1, len(self.items)), 0.08)
        children: list[Primitive] = [surface]
        for row, item in zip(rows, self.items):
            label = str(item.get("label", ""))
            value = max(0.0, min(100.0, float(item.get("value", 0))))
            color = str(item.get("color", "{colors.primary}"))
            children.extend(
                [
                    Text(box=Box(row.x, row.y + 0.02, 1.35, 0.18), text=label, class_names=("progress-label",), style=Style(color="{colors.text_primary}", font_size=ctx.theme.fonts.caption_size, font_weight="bold")),
                    Rect(box=Box(row.x + 1.50, row.y + 0.08, row.w - 2.10, 0.08), class_names=("progress-track",), style=Style(fill="{colors.gray_100}", radius=0.05)),
                    Rect(box=Box(row.x + 1.50, row.y + 0.08, (row.w - 2.10) * value / 100, 0.08), class_names=("progress-fill",), style=Style(fill=color, radius=0.05)),
                    Text(box=Box(row.x + row.w - 0.48, row.y + 0.02, 0.48, 0.16), text=f"{value:.0f}%", class_names=("progress-value",), style=Style(color="{colors.text_secondary}", font_size=8, align="right")),
                ]
            )
        return Group(id=ctx.block_id, class_names=ctx.class_names or ("progress",), children=tuple(children))

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "DataProgressComponent":
        return cls(items=_items(props.get("items", [])))
