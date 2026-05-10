from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ppt_ui.core.component import Component, RenderContext
from ppt_ui.core.layout import Box
from ppt_ui.primitives import Ellipse, Group, Line, Primitive, Rect, Text, normalize_class_names
from ppt_ui.styles import Style


def _items(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _class_names(ctx: RenderContext, props: Mapping[str, Any], *defaults: str) -> tuple[str, ...]:
    value = props.get("class_names", props.get("classes", props.get("class")))
    return (*defaults, *(normalize_class_names(value) or ctx.class_names))


def _primitive_id(ctx: RenderContext, props: Mapping[str, Any]) -> str | None:
    value = props.get("id", ctx.block_id)
    return str(value) if value is not None else None


def _status_colors(status: str) -> tuple[str, str]:
    if status == "done":
        return "{colors.primary}", "{colors.primary_soft}"
    if status in {"active", "current"}:
        return "{colors.accent}", "{colors.accent_soft}"
    return "{colors.gray_200}", "{colors.gray_50}"


@dataclass
class TimelineComponentV2(Component):
    items: list[dict[str, Any]] = field(default_factory=list)
    props: dict[str, Any] = field(default_factory=dict)

    def render_to_primitives(self, ctx: RenderContext, box: Box) -> Group:
        inner = box.inset(0.30, 0.34, 0.30, 0.28)
        line_y = inner.y + 0.22
        slots = inner.split_cols(max(1, len(self.items)), 0.14)
        children: list[Primitive] = [
            Rect(class_names=("timeline-surface",), box=box, style=Style(fill="{colors.surface_white}", stroke="{colors.border}", radius="{radius.md}", shadow=True)),
            Line(x1=inner.x + 0.25, y1=line_y, x2=inner.x + inner.w - 0.25, y2=line_y, style=Style(stroke="{colors.border}", stroke_width=1.0)),
        ]
        for slot, item in zip(slots, self.items):
            status = str(item.get("status", "normal"))
            node_fill, card_fill = _status_colors(status)
            node = Box(slot.x + slot.w / 2 - 0.13, line_y - 0.13, 0.26, 0.26)
            card = Box(slot.x, line_y + 0.38, slot.w, min(max(0.78, slot.h - 0.55), 1.45))
            children.extend(
                [
                    Ellipse(class_names=("timeline-node", f"timeline-node-{status}"), box=node, style=Style(fill=node_fill, stroke="FFFFFF", stroke_width=1.0)),
                    Line(x1=slot.x + slot.w / 2, y1=line_y + 0.16, x2=slot.x + slot.w / 2, y2=card.y, style=Style(stroke=node_fill, stroke_width=0.8)),
                    Rect(class_names=("timeline-card",), box=card, style=Style(fill=card_fill, stroke="{colors.border_light}", radius=0.05)),
                    Text(box=Box(card.x + 0.12, card.y + 0.10, card.w - 0.24, 0.22), text=str(item.get("label", item.get("title", ""))), style=Style(color="{colors.text_primary}", font_size=ctx.theme.fonts.body_size, font_weight="bold", align="center")),
                    Text(box=Box(card.x + 0.12, card.y + 0.38, card.w - 0.24, 0.16), text=str(item.get("date", item.get("time", ""))), style=Style(color="{colors.text_tertiary}", font_size=ctx.theme.fonts.tiny_size, align="center")),
                    Text(box=Box(card.x + 0.14, card.y + 0.62, card.w - 0.28, max(0.18, card.h - 0.70)), text=str(item.get("description", "")), style=Style(color="{colors.text_secondary}", font_size=8, align="center")),
                ]
            )
        return Group(id=_primitive_id(ctx, self.props), class_names=_class_names(ctx, self.props, "timeline"), children=tuple(children))

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "TimelineComponentV2":
        return cls(items=_items(props.get("items", [])), props=dict(props))


@dataclass
class ProcessFlowComponentV2(Component):
    steps: list[dict[str, Any]] = field(default_factory=list)
    props: dict[str, Any] = field(default_factory=dict)

    def render_to_primitives(self, ctx: RenderContext, box: Box) -> Group:
        steps = self.steps[:6]
        inner = box.inset(0.22, 0.24, 0.22, 0.22)
        cells = inner.split_cols(max(1, len(steps)), 0.16)
        children: list[Primitive] = [Rect(class_names=("process-surface",), box=box, style=Style(fill="{colors.surface_white}", stroke="{colors.border}", radius="{radius.md}", shadow=True))]
        for index, (cell, step) in enumerate(zip(cells, steps), start=1):
            card_h = min(cell.h, 1.30)
            card = Box(cell.x, cell.y + max(0, (cell.h - card_h) / 2), cell.w, card_h)
            badge = Box(card.x + 0.14, card.y + 0.14, 0.26, 0.26)
            children.extend(
                [
                    Rect(class_names=("process-card",), box=card, style=Style(fill="{colors.surface_white}", stroke="{colors.border_light}", radius=0.05, shadow=False)),
                    Ellipse(class_names=("process-badge",), box=badge, style=Style(fill="{colors.primary_soft}", stroke="{colors.border_light}")),
                    Text(box=badge.inset(0.02, 0.02), text=f"{index:02d}", style=Style(color="{colors.primary}", font_size=7, font_weight="bold", align="center", valign="middle")),
                    Text(box=Box(card.x + 0.48, card.y + 0.13, card.w - 0.60, 0.20), text=str(step.get("title", step.get("label", ""))), style=Style(color="{colors.text_primary}", font_size=ctx.theme.fonts.caption_size, font_weight="bold")),
                    Text(box=Box(card.x + 0.16, card.y + 0.48, card.w - 0.32, 0.30), text=str(step.get("description", "")), style=Style(color="{colors.text_secondary}", font_size=8)),
                    Text(box=Box(card.x + 0.16, card.y + card.h - 0.30, card.w - 0.32, 0.18), text=str(step.get("output", "")), style=Style(color="{colors.primary_dark}", font_size=7, align="center", valign="middle")),
                ]
            )
            if index < len(cells):
                y = card.y + card.h / 2
                children.append(Line(x1=card.x + card.w + 0.04, y1=y, x2=cells[index].x - 0.05, y2=y, style=Style(stroke="{colors.primary}", stroke_width=0.8)))
        return Group(id=_primitive_id(ctx, self.props), class_names=_class_names(ctx, self.props, "process-flow"), children=tuple(children))

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "ProcessFlowComponentV2":
        return cls(steps=_items(props.get("steps", props.get("items", []))), props=dict(props))


@dataclass
class RoadmapComponentV2(Component):
    items: list[dict[str, Any]] = field(default_factory=list)
    props: dict[str, Any] = field(default_factory=dict)

    def render_to_primitives(self, ctx: RenderContext, box: Box) -> Group:
        inner = box.inset(0.34, 0.30)
        rows = inner.split_rows(max(1, len(self.items)), 0.10)
        children: list[Primitive] = [Rect(class_names=("roadmap-surface",), box=box, style=Style(fill="{colors.surface_white}", stroke="{colors.border}", radius="{radius.md}", shadow=True))]
        palette = [f"{{chart_palette.{index}}}" for index in range(6)]
        for index, (row, item) in enumerate(zip(rows, self.items)):
            start = max(0.0, min(1.0, float(item.get("start", 0))))
            end = max(start + 0.05, min(1.0, float(item.get("end", 1))))
            track = Box(row.x + 1.10, row.y + 0.08, row.w - 1.55, 0.07)
            color = str(item.get("color", palette[index % len(palette)]))
            children.extend(
                [
                    Text(box=Box(row.x, row.y + 0.02, 1.0, 0.18), text=str(item.get("label", "")), style=Style(color="{colors.text_primary}", font_size=8, font_weight="bold")),
                    Rect(box=track, class_names=("roadmap-track",), style=Style(fill="{colors.gray_100}", radius=0.05)),
                    Rect(box=Box(track.x + track.w * start, track.y, track.w * (end - start), track.h), class_names=("roadmap-bar",), style=Style(fill=color, radius=0.05)),
                    Text(box=Box(row.x + row.w - 0.40, row.y + 0.01, 0.40, 0.16), text=str(item.get("period", "")), style=Style(color="{colors.text_tertiary}", font_size=7, align="right")),
                ]
            )
        return Group(id=_primitive_id(ctx, self.props), class_names=_class_names(ctx, self.props, "roadmap"), children=tuple(children))

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "RoadmapComponentV2":
        return cls(items=_items(props.get("items", [])), props=dict(props))


@dataclass
class ModelDiagramComponentV2(Component):
    props: dict[str, Any] = field(default_factory=dict)

    def render_to_primitives(self, ctx: RenderContext, box: Box) -> Group:
        nodes = _items(self.props.get("nodes", []))
        if not nodes:
            labels = self.props.get("stages", ["Input", "Encoder", "Fusion", "Prediction"])
            nodes = [{"label": str(item)} for item in labels]
        inner = box.inset(0.28, 0.30)
        cells = inner.split_cols(max(1, len(nodes)), 0.22)
        children: list[Primitive] = [Rect(class_names=("model-diagram-surface",), box=box, style=Style(fill="{colors.surface_white}", stroke="{colors.border}", radius="{radius.md}", shadow=True))]
        for index, (cell, node) in enumerate(zip(cells, nodes)):
            card = Box(cell.x, cell.y + cell.h / 2 - 0.38, cell.w, 0.76)
            children.extend(
                [
                    Rect(class_names=("model-node",), box=card, style=Style(fill="{colors.primary_soft}" if index in {0, len(nodes) - 1} else "{colors.surface_white}", stroke="{colors.border_light}", radius=0.05)),
                    Text(box=Box(card.x + 0.10, card.y + 0.14, card.w - 0.20, 0.20), text=str(node.get("label", node.get("title", ""))), style=Style(color="{colors.text_primary}", font_size=ctx.theme.fonts.caption_size, font_weight="bold", align="center")),
                    Text(box=Box(card.x + 0.10, card.y + 0.42, card.w - 0.20, 0.18), text=str(node.get("note", node.get("description", ""))), style=Style(color="{colors.text_secondary}", font_size=7, align="center")),
                ]
            )
            if index < len(cells) - 1:
                y = card.y + card.h / 2
                children.append(Line(x1=card.x + card.w + 0.05, y1=y, x2=cells[index + 1].x - 0.05, y2=y, style=Style(stroke="{colors.primary}", stroke_width=0.9)))
        return Group(id=_primitive_id(ctx, self.props), class_names=_class_names(ctx, self.props, "model-diagram"), children=tuple(children))

    @classmethod
    def from_props(cls, props: Mapping[str, Any]) -> "ModelDiagramComponentV2":
        return cls(props=dict(props))
