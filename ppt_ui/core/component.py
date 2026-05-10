from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any
from typing import Protocol

from ppt_ui.core.layout import Box
from ppt_ui.core.layout import SlotNode
from ppt_ui.primitives import Group, Primitive
from ppt_ui.styles import StyleSheet


class SupportsRenderer(Protocol):
    pass


@dataclass(frozen=True)
class ComponentSlot:
    """Stable slot contract exposed by a component.

    Slots are semantic regions such as ``label`` or ``value``. They are not
    absolute coordinates; recipes and containers decide their final boxes.
    """

    name: str
    role: str = "content"
    required: bool = False
    description: str = ""
    default_layout: Mapping[str, Any] = field(default_factory=dict)
    class_name: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", str(self.name))
        object.__setattr__(self, "role", str(self.role))
        object.__setattr__(self, "default_layout", dict(self.default_layout))
        if self.class_name is not None:
            object.__setattr__(self, "class_name", str(self.class_name))

    def to_slot_node(self) -> SlotNode:
        return SlotNode(name=self.name, layout=self.default_layout, metadata={"role": self.role, "class_name": self.class_name})


@dataclass
class RenderContext:
    slide: object
    theme: object
    renderer: SupportsRenderer
    style: dict[str, Any] = field(default_factory=dict)
    stylesheet: StyleSheet = field(default_factory=StyleSheet)
    component_registry: object | None = None
    block_id: str | None = None
    class_names: tuple[str, ...] = ()

    def with_style(self, style: dict[str, Any] | None) -> "RenderContext":
        return replace(self, style=style or {})

    def with_block(self, *, block_id: str | None = None, class_names: tuple[str, ...] = ()) -> "RenderContext":
        return replace(self, block_id=block_id, class_names=tuple(class_names))


@dataclass
class Component:
    @classmethod
    def slot_contract(cls) -> tuple[ComponentSlot, ...]:
        return ()

    @classmethod
    def slot_names(cls) -> tuple[str, ...]:
        return tuple(slot.name for slot in cls.slot_contract())

    def render_to_primitives(self, ctx: RenderContext, box: Box) -> Primitive | Sequence[Primitive]:
        raise NotImplementedError

    def render(self, ctx: RenderContext, box: Box) -> None:
        tree = self.render_to_primitives(ctx, box)
        primitive = Group(children=tuple(tree)) if isinstance(tree, Sequence) and not isinstance(tree, Primitive) else tree
        ctx.renderer.render_tree(ctx.slide, primitive, stylesheet=ctx.stylesheet)
