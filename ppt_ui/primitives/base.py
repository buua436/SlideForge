from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field, replace
from typing import Any

from ppt_ui.core.layout import Box
from ppt_ui.styles import Style


def normalize_class_names(value: str | Iterable[str] | None) -> tuple[str, ...]:
    """Normalize JSON/Python class declarations to a tuple."""

    if value is None:
        return ()
    if isinstance(value, str):
        return tuple(item for item in value.replace(",", " ").split() if item)
    return tuple(str(item) for item in value if str(item))


@dataclass(frozen=True)
class Primitive:
    """Renderer-neutral primitive node.

    Components return primitive trees. Renderers decide how to map each node to
    python-pptx, SVG, HTML preview, or another backend.
    """

    id: str | None = None
    class_names: tuple[str, ...] = ()
    style: Style = field(default_factory=Style)
    box: Box | None = None
    children: tuple["Primitive", ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def type(self) -> str:
        return "primitive"

    def __post_init__(self) -> None:
        object.__setattr__(self, "class_names", normalize_class_names(self.class_names))
        object.__setattr__(self, "children", tuple(self.children))
        if isinstance(self.style, Mapping):
            object.__setattr__(self, "style", Style.from_dict(self.style))

    def with_style(self, style: Style | Mapping[str, Any] | None) -> "Primitive":
        if style is None:
            return self
        next_style = self.style.merge(style)
        return replace(self, style=next_style)

    def walk(self) -> Iterator["Primitive"]:
        yield self
        for child in self.children:
            yield from child.walk()


@dataclass(frozen=True)
class Group(Primitive):
    """A logical primitive group."""

    @property
    def type(self) -> str:
        return "group"
