from dataclasses import dataclass
from typing import Any

from ppt_ui.core.component import RenderContext
from ppt_ui.core.layout import Box
from ppt_ui.core.registry import ComponentRegistry


@dataclass
class DummyComponent:
    name: str

    def render(self, ctx: RenderContext, box: Box) -> None:
        return None


def test_component_registry_tracks_family_variant_and_implementation() -> None:
    registry = ComponentRegistry()
    registry.register("chart.line", lambda props: DummyComponent("shape"), family="chart", implementation="shape")
    registry.register("chart.line", lambda props: DummyComponent("native"), variant="native", family="chart", implementation="native")

    default_component = registry.create("chart.line", {})
    native_component = registry.create("chart.line", {}, variant="native")
    registration = registry.get_registration("chart.line", variant="native")

    assert default_component.name == "shape"
    assert native_component.name == "native"
    assert registration is not None
    assert registration.family == "chart"
    assert registration.variant == "native"
    assert registration.implementation == "native"
    assert registry.variants("chart.line") == ["default", "native"]
    assert registry.type_names_by_family("chart") == ["chart.line"]


def test_component_registry_uses_registered_default_variant() -> None:
    registry = ComponentRegistry()
    registry.register("table.basic", lambda props: DummyComponent("compact"), variant="compact", family="table", default=True)

    assert registry.create("table.basic", {}).name == "compact"
    assert registry.has("table.basic")


def test_component_registry_variant_falls_back_to_default_type() -> None:
    registry = ComponentRegistry()
    registry.register("data.metric_card", lambda props: DummyComponent(str(props.get("label", ""))))

    component = registry.create("data.metric_card", {"label": "Accuracy"}, variant="missing")

    assert component.name == "Accuracy"
