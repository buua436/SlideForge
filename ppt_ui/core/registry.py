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


@dataclass(frozen=True)
class ComponentRegistration:
    type_name: str
    factory: ComponentFactory
    family: str
    variant: str = "default"
    implementation: str = "default"
    default_variant: bool = False

    @property
    def key(self) -> str:
        return ComponentRegistry.key(self.type_name, None if self.variant == "default" else self.variant)


@dataclass
class ComponentRegistry:
    """Registry for block-level component factories."""

    factories: dict[str, ComponentFactory] = field(default_factory=dict)
    registrations: dict[str, ComponentRegistration] = field(default_factory=dict)
    default_variants: dict[str, str] = field(default_factory=dict)

    def register(
        self,
        type_name: str,
        factory: ComponentFactory,
        *,
        variant: str | None = None,
        family: str | None = None,
        implementation: str = "default",
        default: bool = False,
    ) -> None:
        variant_name = variant or "default"
        key = self.key(type_name, None if variant_name == "default" else variant_name)
        registration = ComponentRegistration(
            type_name=type_name,
            factory=factory,
            family=family or self.family_name(type_name),
            variant=variant_name,
            implementation=implementation,
            default_variant=default,
        )
        self.factories[key] = factory
        self.registrations[key] = registration
        if default or (variant_name == "default" and type_name not in self.default_variants):
            self.default_variants[type_name] = variant_name

    def create(self, type_name: str, props: Mapping[str, Any] | None = None, *, variant: str | None = None) -> RenderableComponent:
        factory = self.resolve_factory(type_name, variant)
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

    def resolve_factory(self, type_name: str, variant: str | None = None) -> ComponentFactory | None:
        variant_name = variant if variant not in (None, "", "default") else None
        if variant_name:
            factory = self.factories.get(self.key(type_name, variant_name))
            if factory is not None:
                return factory
        factory = self.factories.get(type_name)
        if factory is not None:
            return factory
        default_variant = self.default_variants.get(type_name)
        if default_variant and default_variant != "default":
            return self.factories.get(self.key(type_name, default_variant))
        return None

    def has(self, type_name: str, *, variant: str | None = None) -> bool:
        return self.resolve_factory(type_name, variant) is not None

    def get_registration(self, type_name: str, *, variant: str | None = None) -> ComponentRegistration | None:
        variant_name = variant if variant not in (None, "", "default") else None
        if variant_name:
            registration = self.registrations.get(self.key(type_name, variant_name))
            if registration is not None:
                return registration
        return self.registrations.get(type_name)

    def variants(self, type_name: str) -> list[str]:
        return sorted(
            registration.variant
            for registration in self.registrations.values()
            if registration.type_name == type_name
        )

    def families(self) -> list[str]:
        return sorted({registration.family for registration in self.registrations.values()})

    def type_names_by_family(self, family: str) -> list[str]:
        return sorted({registration.type_name for registration in self.registrations.values() if registration.family == family})

    def type_names(self) -> list[str]:
        return sorted(self.factories)

    @staticmethod
    def key(type_name: str, variant: str | None = None) -> str:
        return f"{type_name}.{variant}" if variant else type_name

    @staticmethod
    def family_name(type_name: str) -> str:
        return type_name.split(".", 1)[0] if "." in type_name else type_name
