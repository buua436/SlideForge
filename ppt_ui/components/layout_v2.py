from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from ppt_ui.core.component import Component, ComponentSlot, RenderContext
from ppt_ui.core.layout import Box, SlotLayoutEngine, SlotLayoutRecipe, SlotNode
from ppt_ui.core.page import Block
from ppt_ui.primitives import Group, Primitive, Rect, normalize_class_names
from ppt_ui.styles import Style


def _children(value: object) -> list["ContainerChild"]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    children: list[ContainerChild] = []
    for index, item in enumerate(value):
        child = ContainerChild.from_value(item, index)
        if child is not None:
            children.append(child)
    return children


def _style_data(ctx: RenderContext, props: Mapping[str, Any], defaults: Mapping[str, Any]) -> dict[str, Any]:
    data = dict(defaults)
    data.update(dict(ctx.style))
    if isinstance(props.get("style"), Mapping):
        data.update(dict(props["style"]))
    for key in ("fill", "stroke", "border", "color", "radius", "shadow", "opacity", "stroke_width"):
        if key in props:
            data[key] = props[key]
    return data


def _normalize_recipe(spec: object, fallback: Mapping[str, Any]) -> SlotLayoutRecipe:
    if isinstance(spec, Mapping):
        merged = dict(fallback)
        merged.update(dict(spec))
        return SlotLayoutRecipe.from_value(merged)
    if spec is not None:
        return SlotLayoutRecipe.from_value(spec)
    return SlotLayoutRecipe.from_value(fallback)


@dataclass(frozen=True)
class ContainerChild:
    block: Block
    slot_name: str
    slot_layout: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_value(cls, value: object, index: int) -> "ContainerChild | None":
        if isinstance(value, Block):
            return cls(block=value, slot_name=value.id or f"slot_{index + 1}", slot_layout=dict(value.layout))
        if not isinstance(value, Mapping):
            return None
        data = dict(value)
        slot_name = str(data.pop("slot", data.get("id", f"slot_{index + 1}")))
        slot_layout = dict(data.pop("slot_layout", data.get("layout", {})) or {})
        block = Block.from_mapping(data)
        return cls(block=block, slot_name=slot_name, slot_layout=slot_layout)

    def to_slot_node(self) -> SlotNode:
        return SlotNode(name=self.slot_name, layout=self.slot_layout)


@dataclass
class LayoutContainerComponent(Component):
    props: dict[str, Any] = field(default_factory=dict)
    kind: str = "container"

    @classmethod
    def slot_contract(cls) -> tuple[ComponentSlot, ...]:
        return (
            ComponentSlot("root", role="container", required=True, description="Outer container area."),
            ComponentSlot("surface", role="surface", description="Optional container/card surface."),
            ComponentSlot("children", role="collection", description="Recursive child component slots."),
        )

    def render_to_primitives(self, ctx: RenderContext, box: Box) -> Primitive | Sequence[Primitive]:
        surface = self._surface(ctx, box)
        return Group(children=(surface,)) if surface is not None else Group(children=())

    def render(self, ctx: RenderContext, box: Box) -> None:
        surface = self._surface(ctx, box)
        if surface is not None:
            ctx.renderer.render_tree(ctx.slide, surface, stylesheet=ctx.stylesheet)

        children = _children(self.props.get("children", self.props.get("blocks", [])))
        if not children:
            return
        registry = ctx.component_registry
        if registry is None or not hasattr(registry, "create"):
            return

        recipe = self._recipe(ctx)
        slot_result = SlotLayoutEngine().layout(box, [child.to_slot_node() for child in children], recipe)
        for child in children:
            if not child.block.visible:
                continue
            slot = slot_result.slots.get(child.slot_name)
            if slot is None:
                continue
            component = registry.create(child.block.type, child.block.props, variant=child.block.variant)
            theme_style = ctx.theme.component_default_style(child.block.type, child.block.variant)
            component_style = {**theme_style, **child.block.style}
            child_ctx = ctx.with_block(block_id=child.block.id, class_names=child.block.class_names).with_style(component_style)
            component.render(child_ctx, slot.box)

    def _recipe(self, ctx: RenderContext) -> SlotLayoutRecipe:
        default_gap = getattr(ctx.theme.spacing, "gutter", 0.16)
        default_padding = 0.0
        model = self.props.get("model")
        fallback: dict[str, Any]
        if self.kind == "grid":
            fallback = {
                "model": "grid",
                "columns": int(self.props.get("columns", 2)),
                "rows": int(self.props.get("rows", 1)),
                "gap": float(self.props.get("gap", default_gap)),
                "padding": self.props.get("padding", default_padding),
            }
        elif self.kind in {"stack", "container"}:
            fallback = {
                "model": model or self.props.get("direction", "stack"),
                "gap": float(self.props.get("gap", default_gap)),
                "padding": self.props.get("padding", default_padding),
            }
        else:
            fallback = {
                "model": model or self.props.get("direction", "stack"),
                "gap": float(self.props.get("gap", default_gap)),
                "padding": self.props.get("padding", getattr(ctx.theme.spacing, "card_padding", 0.18)),
            }
        if fallback["model"] in {"vertical", "column"}:
            fallback["model"] = "stack"
        if fallback["model"] in {"horizontal", "row"}:
            fallback["model"] = "row"
        return _normalize_recipe(self.props.get("recipe", self.props.get("slot_layout")), fallback)

    def _surface(self, ctx: RenderContext, box: Box) -> Rect | None:
        defaults: dict[str, Any] = {}
        if self.kind == "card":
            defaults = {"fill": "{colors.surface_white}", "stroke": "{colors.border}", "radius": "{radius.md}", "shadow": True}
        elif self.kind == "container":
            defaults = {"fill": None, "stroke": None, "shadow": False}

        style = Style.from_dict(_style_data(ctx, self.props, defaults))
        has_surface = self.kind == "card" or style.fill is not None or style.stroke is not None or bool(style.shadow)
        if not has_surface:
            return None
        return Rect(
            id=str(self.props["id"]) if self.props.get("id") is not None else ctx.block_id,
            class_names=(*normalize_class_names(self.props.get("class", self.props.get("class_names"))), f"layout-{self.kind}"),
            box=box,
            style=style,
        )

    @classmethod
    def from_props(cls, props: Mapping[str, Any], *, kind: str = "container") -> "LayoutContainerComponent":
        return cls(props=dict(props), kind=kind)
