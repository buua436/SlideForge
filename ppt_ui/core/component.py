from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any
from typing import Protocol

from ppt_ui.core.layout import Box


class SupportsRenderer(Protocol):
    pass


@dataclass
class RenderContext:
    slide: object
    theme: object
    renderer: SupportsRenderer
    style: dict[str, Any] = field(default_factory=dict)

    def with_style(self, style: dict[str, Any] | None) -> "RenderContext":
        return replace(self, style=style or {})


@dataclass
class Component:
    def render(self, ctx: RenderContext, box: Box) -> None:
        raise NotImplementedError
