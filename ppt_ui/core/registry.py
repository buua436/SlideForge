from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol

from ppt_ui.core.component import RenderContext
from ppt_ui.core.diagnostics import Diagnostic, DiagnosticError
from ppt_ui.core.layout import Box


class RenderableComponent(Protocol):
    def render(self, ctx: RenderContext, box: Box) -> None:
        raise NotImplementedError


ComponentFactory = Callable[[Mapping[str, Any]], RenderableComponent]


@dataclass
class ComponentRegistry:
    """Registry for block-level component factories."""

    factories: dict[str, ComponentFactory] = field(default_factory=dict)

    def register(self, type_name: str, factory: ComponentFactory, *, variant: str | None = None) -> None:
        self.factories[self.key(type_name, variant)] = factory

    def create(self, type_name: str, props: Mapping[str, Any] | None = None) -> RenderableComponent:
        factory = self.factories.get(type_name)
        if factory is None:
            raise DiagnosticError(
                [
                    Diagnostic(
                        "error",
                        "UNKNOWN_COMPONENT_TYPE",
                        f"Unsupported component type: {type_name}",
                        suggestion=f"Use one of: {', '.join(self.type_names())}",
                    )
                ]
            )
        return factory(props or {})

    def has(self, type_name: str) -> bool:
        return type_name in self.factories

    def type_names(self) -> list[str]:
        return sorted(self.factories)

    @staticmethod
    def key(type_name: str, variant: str | None = None) -> str:
        return f"{type_name}.{variant}" if variant else type_name
